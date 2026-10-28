"""本机 HTTP API：返回结构化结果，不调用终端输入或报告排版。"""

from datetime import datetime, timedelta, timezone
from functools import lru_cache
import logging
import os
from typing import Any, Dict, List, Literal, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException

from birth_time import resolve_local_time
from calculator import bazi
from fortune import lots
from i18n import t
from people import PEOPLE, prepare_people, recommend_people
from rules import data_loader, interpretation


Language = Literal["zh", "en"]
Topic = Literal["wealth", "study", "romance"]
API_VERSION = "1.0.0"
CALCULATION_ZONE = timezone(timedelta(hours=8))
logger = logging.getLogger(__name__)

ERROR_MESSAGES = {
    "zh": {
        "invalid_request": "请求参数不正确，请检查 details 中标出的字段。",
        "invalid_birth": "出生日期或时间无效，请使用 YYYY-MM-DD 和 HH:MM。",
        "invalid_timezone": "出生时区无效，请使用 Asia/Shanghai 等 IANA 时区名称。",
        "birth_out_of_range": "出生时间超出了时区换算范围。",
        "time_nonexistent": "这个当地钟点因时钟调整而不存在，请核对出生记录。",
        "time_ambiguous": "这个当地钟点出现过两次，请根据 candidates 选择 fold=0 或 fold=1 后重新请求。",
        "invalid_fold": "这个当地钟点只出现一次，无需指定第二次；请省略 fold 或设为 0。",
        "birth_in_future": "出生时间不能晚于当前时间。",
        "calculation_unavailable": "这个出生时间暂时无法排盘，请核对出生信息。",
        "rules_unavailable": "规则文件暂时无法读取，请检查本地规则文件。",
        "people_unavailable": "人物资料暂时无法准备，请检查本地人物资料。",
        "not_found": "接口不存在。",
        "method_not_allowed": "这个接口不支持所用的请求方法。",
        "internal_error": "服务暂时无法完成请求，请稍后重试。"
    },
    "en": {
        "invalid_request": "Invalid request parameters. Check the fields listed in details.",
        "invalid_birth": "Invalid birth date or time. Use YYYY-MM-DD and HH:MM.",
        "invalid_timezone": "Invalid birth time zone. Use an IANA name such as Asia/Shanghai.",
        "birth_out_of_range": "The birth time is outside the supported time zone range.",
        "time_nonexistent": "This local time did not exist because of a clock change. Check the birth record.",
        "time_ambiguous": "This local time occurred twice. Select fold=0 or fold=1 from candidates and submit again.",
        "invalid_fold": "This local time occurred only once. Omit fold or set it to 0.",
        "birth_in_future": "The birth time cannot be in the future.",
        "calculation_unavailable": "A chart cannot be calculated for this birth time. Check the birth details.",
        "rules_unavailable": "The rules are temporarily unavailable. Check the local rules files.",
        "people_unavailable": "The people data is temporarily unavailable. Check the local records.",
        "not_found": "API endpoint not found.",
        "method_not_allowed": "This endpoint does not support that request method.",
        "internal_error": "The service cannot complete the request right now. Please try again later."
    }
}


class BirthInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    date: str = Field(pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$", examples=["2003-04-01"])
    time: str = Field(pattern=r"^[0-9]{2}:[0-9]{2}$", examples=["14:15"])
    timezone: str = Field(default="Asia/Shanghai", min_length=1, max_length=100)
    fold: Optional[int] = Field(
        default=None, strict=True, ge=0, le=1,
        description="仅重复钟点需要：0 为第一次，1 为第二次。"
    )


class BirthRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    birth: BirthInput
    language: Language = "zh"


class ReportRequest(BirthRequest):
    topic: Topic = "wealth"


class DrawRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic: Topic = "wealth"
    language: Language = "zh"


class PeopleRequest(BirthRequest):
    limit: int = Field(default=3, strict=True, ge=1, le=3)


class ResolvedBirth(BaseModel):
    local_datetime: datetime
    timezone: str
    utc_datetime: datetime
    calculation_datetime: datetime
    fold: int


class Pillars(BaseModel):
    year: str
    month: str
    day: str
    time: str


class Chart(BaseModel):
    pillars: Pillars
    element_counts: Dict[str, int]


class ReadingItem(BaseModel):
    element: str
    title: str
    basis: str
    text: str
    advice: str


class Reading(BaseModel):
    topic: Topic
    topic_label: str
    dominant_elements: List[str]
    missing_elements: List[str]
    text: str
    items: List[ReadingItem]


class ChartResponse(BaseModel):
    language: Language
    birth: ResolvedBirth
    chart: Chart
    element_labels: Dict[str, str]
    calculation_note: str
    notice: str


class ReportResponse(ChartResponse):
    reading: Reading


class Lot(BaseModel):
    id: int
    topic: Topic
    topic_label: str
    title: str
    text: str
    interpretation: str
    advice: str


class DrawResponse(BaseModel):
    language: Language
    lot: Lot
    notice: str


class PersonInfo(BaseModel):
    id: str
    name: str
    birth: str
    timezone: str
    birth_source: str
    dominant_elements: List[str]
    element_counts: Dict[str, int]


class Biography(BaseModel):
    summary: str
    url: str
    available: bool


class PersonMatch(BaseModel):
    person: PersonInfo
    common_elements: List[str]
    same_dominant: bool
    match_label: str
    biography: Biography


class PeopleResponse(BaseModel):
    language: Language
    birth: ResolvedBirth
    dominant_elements: List[str]
    element_labels: Dict[str, str]
    people: List[PersonMatch]
    notice: str


class TopicInfo(BaseModel):
    id: Topic
    label: str
    description: str


class TopicsResponse(BaseModel):
    language: Language
    topics: List[TopicInfo]


class City(BaseModel):
    id: str
    label: str
    timezone: str


class CitiesResponse(BaseModel):
    language: Language
    cities: List[City]


class HealthResponse(BaseModel):
    status: str
    api_version: str


class ErrorInfo(BaseModel):
    code: str
    message: str
    details: Any = None


class ErrorResponse(BaseModel):
    error: ErrorInfo


class APIError(Exception):
    def __init__(self, code, language="zh", details=None, status_code=422):
        super().__init__(code)
        self.code = code
        self.language = language
        self.details = details
        self.status_code = status_code


app = FastAPI(
    title="Suanming API",
    version=API_VERSION,
    description="八字表层五行、主题解读、抽签与相似人物。language 支持 zh/en，各功能独立返回 JSON。",
    responses={
        422: {"model": ErrorResponse, "description": "请求或出生时间无效"},
        503: {"model": ErrorResponse, "description": "本地资料暂时不可用"},
        500: {"model": ErrorResponse, "description": "服务内部错误"}
    }
)

default_origins = ",".join(
    f"http://{host}:{port}"
    for host in ("localhost", "127.0.0.1")
    for port in (3000, 5173, 8080)
)
origins = [
    origin.strip()
    for origin in os.getenv("SUANMING_CORS_ORIGINS", default_origins).split(",")
    if origin.strip()
]
def error_response(code, language="zh", details=None, status_code=422, headers=None):
    return JSONResponse(
        status_code=status_code,
        headers=headers,
        content={"error": {
            "code": code,
            "message": ERROR_MESSAGES[language][code],
            "details": details
        }}
    )


def request_language(request, body=None):
    current = getattr(request.state, "language", None)
    if current in ("zh", "en"):
        return current
    if isinstance(body, dict) and body.get("language") in ("zh", "en"):
        return body["language"]
    language = request.query_params.get("language", "zh")
    return language if language in ("zh", "en") else "zh"


@app.exception_handler(APIError)
async def handle_api_error(request: Request, error: APIError):
    return error_response(error.code, error.language, error.details, error.status_code)


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, error: RequestValidationError):
    details = [
        {"field": ".".join(str(part) for part in item["loc"]), "type": item["type"]}
        for item in error.errors()
    ]
    return error_response("invalid_request", request_language(request, error.body), details)


@app.exception_handler(HTTPException)
async def handle_http_error(request: Request, error: HTTPException):
    code = {404: "not_found", 405: "method_not_allowed"}.get(error.status_code, "internal_error")
    return error_response(
        code, request_language(request), status_code=error.status_code, headers=error.headers
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, error: Exception):
    logger.exception("API request failed")
    return error_response("internal_error", request_language(request), status_code=500)


def load_rules(language):
    try:
        return data_loader(language)
    except (OSError, ValueError) as error:
        raise APIError("rules_unavailable", language, status_code=503) from error


def resolve_birth(data, language):
    try:
        local_birth = datetime.strptime(data.date + " " + data.time, "%Y-%m-%d %H:%M")
    except ValueError as error:
        raise APIError("invalid_birth", language) from error

    try:
        ZoneInfo(data.timezone)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise APIError("invalid_timezone", language) from error

    try:
        candidates = resolve_local_time(local_birth, data.timezone)
    except (OverflowError, ValueError) as error:
        raise APIError("birth_out_of_range", language) from error

    if not candidates:
        raise APIError("time_nonexistent", language)

    if len(candidates) == 2 and data.fold is None:
        raise APIError("time_ambiguous", language, details={"candidates": [
            {
                "fold": candidate.fold,
                "local_datetime": candidate.isoformat(),
                "utc_datetime": candidate.astimezone(timezone.utc).isoformat()
            }
            for candidate in candidates
        ]})

    if len(candidates) == 1:
        if data.fold == 1:
            raise APIError("invalid_fold", language)
        birth = candidates[0]
    else:
        birth = next(candidate for candidate in candidates if candidate.fold == data.fold)

    if birth.astimezone(timezone.utc) > datetime.now(timezone.utc):
        raise APIError("birth_in_future", language)

    return birth


def calculate_chart(data, language):
    birth = resolve_birth(data, language)
    try:
        chart = bazi(birth)
    except (ValueError, IndexError, OverflowError) as error:
        raise APIError("calculation_unavailable", language) from error
    return birth, chart


def birth_response(birth):
    return {
        "local_datetime": birth,
        "timezone": str(birth.tzinfo),
        "utc_datetime": birth.astimezone(timezone.utc),
        "calculation_datetime": birth.astimezone(CALCULATION_ZONE),
        "fold": birth.fold
    }


def element_labels(language):
    return {element: t(element, language) for element in ("木", "火", "土", "金", "水")}


def chart_response(birth, chart, language):
    return {
        "language": language,
        "birth": birth_response(birth),
        "chart": chart,
        "element_labels": element_labels(language),
        "calculation_note": t("calculation_note", language),
        "notice": t("report_notice", language)
    }


@lru_cache(maxsize=1)
def prepared_people():
    return prepare_people(PEOPLE)


@app.get("/", include_in_schema=False)
def index():
    return RedirectResponse("/docs")


@app.get("/api/health", response_model=HealthResponse, tags=["基础信息"])
def health():
    """检查服务是否运行；不排盘、不读取人物、不请求百科。"""
    return {"status": "ok", "api_version": API_VERSION}


@app.get("/api/topics", response_model=TopicsResponse, tags=["基础信息"])
def topics(language: Language = Query(default="zh")):
    rules = load_rules(language)
    return {"language": language, "topics": [
        {"id": topic, **rules["topics"][topic]}
        for topic in ("wealth", "study", "romance")
    ]}


@app.get("/api/cities", response_model=CitiesResponse, tags=["基础信息"])
def cities(language: Language = Query(default="zh")):
    values = [
        ("shanghai", "Asia/Shanghai"),
        ("sydney", "Australia/Sydney"),
        ("london", "Europe/London"),
        ("new_york", "America/New_York"),
        ("tokyo", "Asia/Tokyo")
    ]
    return {"language": language, "cities": [
        {"id": city, "label": t("city_" + city, language), "timezone": zone}
        for city, zone in values
    ]}


@app.post("/api/chart", response_model=ChartResponse, tags=["出生信息"])
def chart(payload: BirthRequest, request: Request):
    """首页填写或更新出生信息时验证并排盘，不产生主题解读、签文或人物。"""
    request.state.language = payload.language
    birth, chart_data = calculate_chart(payload.birth, payload.language)
    return chart_response(birth, chart_data, payload.language)


@app.post("/api/report", response_model=ReportResponse, tags=["主题解读"])
def report(payload: ReportRequest, request: Request):
    """仅返回所选主题的排盘及解读，不抽签、不查询人物。"""
    request.state.language = payload.language
    birth, chart_data = calculate_chart(payload.birth, payload.language)
    rules = load_rules(payload.language)
    result = chart_response(birth, chart_data, payload.language)
    result["reading"] = interpretation(
        chart_data, rules, topic=payload.topic, language=payload.language
    )
    return result


@app.post("/api/draw", response_model=DrawResponse, tags=["主题抽签"])
def draw(payload: DrawRequest, request: Request):
    """只抽取所选主题的一支签，不使用出生信息、不查询人物。"""
    request.state.language = payload.language
    rules = load_rules(payload.language)
    return {
        "language": payload.language,
        "lot": lots(rules, topic=payload.topic),
        "notice": t("entertainment_notice", payload.language)
    }


@app.post("/api/people", response_model=PeopleResponse, tags=["相似人物"])
def people(payload: PeopleRequest, request: Request):
    """只查询最多三位相似人物；百科不可用时保留匹配和原文链接。"""
    request.state.language = payload.language
    birth, chart_data = calculate_chart(payload.birth, payload.language)
    try:
        prepared = prepared_people()
    except (OSError, ValueError, IndexError, OverflowError) as error:
        raise APIError("people_unavailable", payload.language, status_code=503) from error

    counts = chart_data["element_counts"]
    max_count = max(counts.values())
    dominant = [element for element, count in counts.items() if count == max_count]
    matches = recommend_people(dominant, prepared, language=payload.language, limit=payload.limit)
    results = []

    for match in matches:
        person = match["person"]
        biography = match["biography"]
        results.append({
            "person": {
                "id": person["wiki_titles"]["en"],
                "name": person["name"] if payload.language == "zh" else person["wiki_titles"]["en"],
                "birth": person["birth"],
                "timezone": person["timezone"],
                "birth_source": person["birth_source"],
                "dominant_elements": person["dominant_elements"],
                "element_counts": person["element_counts"]
            },
            "common_elements": match["common_elements"],
            "same_dominant": match["same_dominant"],
            "match_label": t("match_exact" if match["same_dominant"] else "match_partial", payload.language),
            "biography": {
                "summary": biography["summary"],
                "url": biography["url"],
                "available": biography["available"]
            }
        })

    return {
        "language": payload.language,
        "birth": birth_response(birth),
        "dominant_elements": dominant,
        "element_labels": element_labels(payload.language),
        "people": results,
        "notice": t("people_notice", payload.language)
    }


# 放在最外层，让意外 500 响应也携带 CORS 头，网页仍能读取错误 JSON。
app = CORSMiddleware(
    app,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"]
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
