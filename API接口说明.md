# Suanming API 使用说明

项目目录：`/Users/liuliu/Desktop/suanming`。本机 HTTP API 已实现，中英文共用现有排盘、规则、抽签和人物匹配逻辑。终端程序仍可使用原来的启动方式。

2026-10-29：已新增 Render 部署配置。公网创建步骤见[Render部署说明](Render部署说明.md)，网页接入见[Lovable公网接入补充说明](Lovable公网接入补充说明.md)。目前还没有真实线上服务地址；下文的本机地址仅用于本地测试。

## 1. 启动与停止

当前电脑的 API 专用环境 `.venv-api` 已创建，使用 Python 3.12.14，依赖也已安装。无需重复安装，终端运行：

```bash
cd /Users/liuliu/Desktop/suanming
./.venv-api/bin/python3 api.py
```

保持该终端运行，在浏览器打开：

- [交互测试页面](http://127.0.0.1:8000/docs)
- [健康检查](http://127.0.0.1:8000/api/health)
- [OpenAPI 接口描述](http://127.0.0.1:8000/openapi.json)

正常启动后，终端会保持等待请求。回到这个终端按 `Ctrl+C` 停止服务。

如果 8000 端口已被占用，可改用：

```bash
./.venv-api/bin/python3 -m uvicorn api:app --host 127.0.0.1 --port 8001
```

此时浏览器使用 `http://127.0.0.1:8001/docs`。

终端菜单仍使用：

```bash
./.venv/bin/python3 main.py
```

两套环境分开，API 安装没有升级原来的终端环境。API 的固定依赖在 `requirements-api.txt`，测试依赖在 `requirements-dev.txt`。以后在另一台已安装 Python 3.12 的电脑上重建时，可使用：

```bash
python3.12 -m venv .venv-api
./.venv-api/bin/python3 -m pip install -r requirements-api.txt
```

## 2. 接口列表

| 方法 | 地址 | 输入与用途 |
| --- | --- | --- |
| GET | `/api/health` | 服务状态，不排盘、不查询人物 |
| GET | `/api/topics?language=zh` | 三个主题的编号、名称和说明 |
| GET | `/api/cities?language=zh` | 五个常用出生城市及其 IANA 时区 |
| POST | `/api/chart` | 验证出生信息并返回四柱、五行，不生成其他内容 |
| POST | `/api/report` | 出生信息、语言与主题，只返回对应解读及排盘 |
| POST | `/api/draw` | 语言与主题，只返回一支签 |
| POST | `/api/people` | 出生信息与语言，只返回最多三位相似人物 |

语言值为 `zh` 或 `en`，默认 `zh`。主题值为 `wealth`（财运）、`study`（学习运）、`romance`（桃花运），报告与抽签默认 `wealth`。不支持的语言、主题及多余输入字段都会返回参数错误。

API 不保存账号、生日或用户会话。网页继续按已确认的流程工作：先填写出生信息，调用 `/api/chart` 成功后显示单层功能菜单；用户选哪项，网页就只请求和展示对应接口结果。后续报告和人物请求由网页再次附带同一份出生信息，修改生日时更新网页保存的这份信息。

抽签算法不使用生日，因此 `/api/draw` 只接收主题和语言；“先填写出生信息”的顺序由终端或未来网页界面执行。API 返回 JSON，不使用终端输入，也没有终端的“输入 0 退出”操作；停止 API 服务使用 `Ctrl+C`。

## 3. 先在浏览器测试

打开 `/docs`：

1. 展开 `POST /api/report`。
2. 点击 `Try it out`。
3. 将 Request body 替换为下面内容。
4. 点击 `Execute`，查看 `Server response` 中的状态码与 JSON。

```json
{
  "language": "zh",
  "topic": "study",
  "birth": {
    "date": "2003-04-01",
    "time": "14:15",
    "timezone": "Asia/Shanghai"
  }
}
```

预期 HTTP 状态码 `200`，其中排盘为：

```json
{
  "pillars": {
    "year": "癸未",
    "month": "乙卯",
    "day": "甲辰",
    "time": "辛未"
  },
  "element_counts": {
    "木": 3,
    "火": 0,
    "土": 3,
    "金": 1,
    "水": 1
  }
}
```

上面这一段位于响应的 `chart` 字段。完整响应还包括：

- `birth`：当地带偏移的出生时间、时区、UTC 时间、用于排盘的固定 UTC+8 时间及 `fold`。
- `reading`：主题、最多项、未出现项、正文，以及带标题、依据、正文和行动提示的 `items`。
- `element_labels`：原始五行键对应的显示名称。
- `calculation_note` 和 `notice`：当前语言的计算说明与娱乐提示。

解读响应没有 `lot` 或人物列表。把 `language` 改成 `en` 后，文案、动态依据、提示和 `element_labels` 会显示英文；四柱干支符号与原始五行键保持稳定。例如 `element_labels["木"]` 为 `Wood`，计数仍通过 `chart.element_counts["木"]` 读取。

## 4. 出生信息验证与排盘

`POST /api/chart` 请求：

```json
{
  "language": "zh",
  "birth": {
    "date": "2003-04-01",
    "time": "14:15",
    "timezone": "Asia/Shanghai"
  }
}
```

响应包含出生信息与 `chart`，没有主题解读。日期必须为公历 `YYYY-MM-DD`，时间为 24 小时制 `HH:MM`，使用英文冒号。先按出生地时区判断实际时刻，再换算为固定 UTC+8 排盘，和终端一致。

可使用 `/api/cities` 的五个时区，也接受其他有效 IANA 时区，例如 `Europe/Paris`。不使用含义可能不明确的 `CST` 等缩写。省略 `timezone` 时默认 `Asia/Shanghai`。

### 重复钟点

例如悉尼 `2024-04-07 02:30` 发生过两次。第一次不传 `fold`：

```json
{
  "language": "zh",
  "birth": {
    "date": "2024-04-07",
    "time": "02:30",
    "timezone": "Australia/Sydney"
  }
}
```

接口返回 `422`，错误码为 `time_ambiguous`；`error.details.candidates` 提供两种当地偏移与对应 UTC 时间。根据出生记录选择后，在 `birth` 中加入：

```json
"fold": 1
```

- `fold: 0` 表示第一次，当地偏移为 `+11:00`。
- `fold: 1` 表示第二次，当地偏移为 `+10:00`。

这里使用程序标准的 `0/1`，与终端显示的“第 1 次／第 2 次”选项编号不同。普通钟点省略 `fold` 即可；给普通钟点指定 `fold: 1` 会返回 `invalid_fold`。

悉尼 `2024-10-06 02:30` 因夏令时切换而不存在，会返回 `time_nonexistent`。出生时间在未来、日期不存在、时间格式不符或时区无效也都会拒绝。

## 5. 独立抽签

`POST /api/draw` 请求：

```json
{
  "language": "en",
  "topic": "study"
}
```

响应字段为 `language`、`lot` 和 `notice`。`lot` 包含 `id/topic/topic_label/title/text/interpretation/advice`。只会从所选主题的三支签中抽取，重复抽到同一支正常。

本接口不会返回四柱、解读报告或人物。没有额外的抽签动画逻辑。

## 6. 相似人物

`POST /api/people` 请求：

```json
{
  "language": "en",
  "limit": 3,
  "birth": {
    "date": "2003-04-01",
    "time": "14:15",
    "timezone": "Asia/Shanghai"
  }
}
```

`limit` 为整数 1～3，默认 3。响应的 `people` 列表中，每项包含：

- `person`：稳定的英文词条标识 `id`、当前语言姓名、公开出生资料及来源、人物五行计数和最多项。
- `common_elements` 和 `same_dominant`：共同最多项与是否为相同的最多项集合。
- `match_label`：当前语言的匹配方式说明。
- `biography`：`summary`、`url`、`available`。

本样例应匹配 Elvis Presley、Pope Benedict XVI、Serge Gainsbourg。匹配算法、30 位资料与终端共用，不要求先请求某个主题解读。

人物库在 API 进程内首次使用时准备，后续复用；没有用户生日缓存、数据库或持久历史。每次调用人物接口都会获取本次入选人物的简介，最多三个请求，每个请求设置 8 秒网络超时。切换网页主题无需再次请求人物接口；网页可以在当前页面内复用已收到的结果。

如果百科不可用，仍返回 `200` 和人物匹配结果，`biography.available` 为 `false`，`summary` 为当前语言的备用提示，`url` 仍提供百科原文链接。接口不把内部原始网络错误返回给网页。

## 7. 错误格式

错误响应统一为：

```json
{
  "error": {
    "code": "birth_in_future",
    "message": "出生时间不能晚于当前时间。",
    "details": null
  }
}
```

`code` 保持语言无关，`message` 根据合法的 `language` 参数翻译。参数验证失败时，`details` 会列出字段路径与错误类型，例如 `body.birth.date`。语言本身无效时默认使用中文错误提示。

| 状态码 | 常见 code | 含义 |
| --- | --- | --- |
| 422 | `invalid_request` | 缺字段、无效语言或主题、格式不符、额外字段、非法 limit/fold 等 |
| 422 | `invalid_birth` | 形式符合但实际不存在的日期或时间 |
| 422 | `invalid_timezone` | 无效的 IANA 时区 |
| 422 | `time_nonexistent` | 当地钟点不存在 |
| 422 | `time_ambiguous` | 当地钟点重复，需要提交 fold |
| 422 | `invalid_fold` | 普通钟点指定了第二次 |
| 422 | `birth_in_future` | 出生时间晚于当前时刻 |
| 422 | `birth_out_of_range` / `calculation_unavailable` | 无法换算时区或排盘 |
| 503 | `rules_unavailable` / `people_unavailable` | 本地业务资料暂时无法读取或准备 |
| 404 / 405 | `not_found` / `method_not_allowed` | 接口地址或 HTTP 方法错误 |
| 500 | `internal_error` | 未预期的服务错误，响应不包含堆栈 |

## 8. 用终端发送请求

服务运行时，另开一个终端，执行：

```bash
curl http://127.0.0.1:8000/api/health
```

中文学习运解读：

```bash
curl -X POST http://127.0.0.1:8000/api/report \
  -H 'Content-Type: application/json' \
  -d '{"language":"zh","topic":"study","birth":{"date":"2003-04-01","time":"14:15","timezone":"Asia/Shanghai"}}'
```

英文财运抽签：

```bash
curl -X POST http://127.0.0.1:8000/api/draw \
  -H 'Content-Type: application/json' \
  -d '{"language":"en","topic":"wealth"}'
```

## 9. 本地网页与 Lovable 后续接入

默认允许的网页来源为：

```text
http://localhost:3000
http://127.0.0.1:3000
http://localhost:5173
http://127.0.0.1:5173
http://localhost:8080
http://127.0.0.1:8080
```

如果网页地址不同，在启动前通过环境变量指定完整来源；多个来源用逗号分隔，端口也属于来源的一部分。例如：

```bash
SUANMING_CORS_ORIGINS='http://localhost:5173,http://localhost:4173' ./.venv-api/bin/python3 api.py
```

指定后会替换默认列表。当前接口没有登录，不携带登录凭据。

当前服务只绑定 `127.0.0.1`，是本机 HTTP，只有本机能访问。未来 Lovable 公网网页需要后端可访问的 HTTPS 地址，并配置对应的网页来源。当前没有部署公网服务，也尚未安装本地可信证书；HTTPS 是下一步，不能把本机 HTTP 地址作为已经完成的公网 HTTPS 接口。

接口结构可从运行中的 `/openapi.json` 获取，也已导出到项目的 `openapi.json`，方便后续交给网页开发工具。

## 10. 自动检查与文件关系

测试依赖已装在 API 环境，运行：

```bash
./.venv-api/bin/python3 -m unittest discover -s tests -v
```

以后重建测试环境可先安装：

```bash
./.venv-api/bin/python3 -m pip install -r requirements-dev.txt
```

测试使用实际排盘与业务规则，百科请求使用模拟结果，避免外部网络影响检查。真实百科可在浏览器测试 `/api/people`。

```text
api.py → birth_time.py（真实当地时间解析）
       → calculator.py（四柱与表层五行）
       → rules.py / rules*.json（主题解读）
       → fortune.py（抽签）
       → people.py（相似人物与百科简介）

main.py → user.py → birth_time.py
```

终端与 API 共用时间往返校验，API 不导入或调用终端输入层。接口返回结构化数据；网页自行排版，不需要解析 `report.py` 的终端文本。

参考：[FastAPI 基础接口](https://fastapi.tiangolo.com/tutorial/first-steps/)、[FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/)、[Starlette CORS 全局设置](https://starlette.dev/middleware/#corsmiddleware-global-enforcement)、[Uvicorn HTTPS 参数](https://uvicorn.dev/settings/#https)。
