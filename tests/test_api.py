"""HTTP contract checks for the local API; all encyclopedia requests stay offline."""

from contextlib import ExitStack
from copy import deepcopy
from datetime import datetime, timedelta
from io import BytesIO
import json
import os
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

from fastapi.testclient import TestClient

import api as api_module
from rules import data_loader


SAMPLE_BIRTH = {
    "date": "2003-04-01",
    "time": "14:15",
    "timezone": "Asia/Shanghai"
}
SAMPLE_CHART = {
    "pillars": {
        "year": "癸未", "month": "乙卯", "day": "甲辰", "time": "辛未"
    },
    "element_counts": {"木": 3, "火": 0, "土": 3, "金": 1, "水": 1}
}
TOPICS = ("wealth", "study", "romance")
LANGUAGES = ("zh", "en")
UPSTREAM_ERROR = "PRIVATE_UPSTREAM_CONNECTION_DETAIL"


def birth_payload(language="zh", **birth_changes):
    birth = {**SAMPLE_BIRTH, **birth_changes}
    return {"birth": birth, "language": language}


def parse_datetime(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def wikipedia_response(request, timeout=8):
    """Return a fresh readable response for the real biography parser."""
    parsed = urlsplit(request.full_url)
    title = unquote(parsed.path.rsplit("/", 1)[-1])
    language = parsed.hostname.split(".")[0]
    data = {
        "extract": f"Offline biography fixture: {title} ({language}).",
        "content_urls": {
            "desktop": {"page": f"https://{parsed.hostname}/wiki/{title}"}
        }
    }
    return BytesIO(json.dumps(data).encode("utf-8"))


class APIContractTests(unittest.TestCase):
    def setUp(self):
        self.stack = self.enterContext(ExitStack())
        self.terminal_input = self.stack.enter_context(
            patch("builtins.input", side_effect=AssertionError("API must not read terminal input"))
        )
        self.wikipedia = self.stack.enter_context(
            patch("people.urlopen", side_effect=OSError(UPSTREAM_ERROR))
        )
        self.client = self.stack.enter_context(
            TestClient(api_module.app, raise_server_exceptions=False)
        )

    def tearDown(self):
        self.terminal_input.assert_not_called()

    def assert_error(self, response, code=None, status=422):
        self.assertEqual(response.status_code, status, response.text)
        self.assertIn("application/json", response.headers.get("content-type", ""))
        body = response.json()
        self.assertEqual(set(body), {"error"})
        self.assertEqual(set(body["error"]), {"code", "message", "details"})
        self.assertIsInstance(body["error"]["message"], str)
        self.assertTrue(body["error"]["message"])
        if code is not None:
            self.assertEqual(body["error"]["code"], code)
        self.assertNotIn("Traceback", response.text)
        return body["error"]

    def forbid_business_calls(self, *names):
        return [
            self.stack.enter_context(
                patch.object(api_module, name, side_effect=AssertionError(f"Unexpected {name} call"))
            )
            for name in names
        ]

    def test_health_does_not_load_rules_calculate_or_fetch_people(self):
        calls = self.forbid_business_calls(
            "data_loader", "bazi", "interpretation", "lots",
            "prepare_people", "recommend_people"
        )
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["status"], "ok")
        self.assertTrue(response.json()["api_version"])
        for call in calls:
            call.assert_not_called()
        self.wikipedia.assert_not_called()

    def test_topics_and_cities_return_only_local_metadata_in_both_languages(self):
        calls = self.forbid_business_calls("bazi", "lots", "prepare_people", "recommend_people")
        labels = {}
        for language in LANGUAGES:
            with self.subTest(language=language):
                response = self.client.get("/api/topics", params={"language": language})
                self.assertEqual(response.status_code, 200, response.text)
                body = response.json()
                self.assertEqual(set(body), {"language", "topics"})
                self.assertEqual(body["language"], language)
                self.assertEqual([topic["id"] for topic in body["topics"]], list(TOPICS))
                self.assertTrue(all(topic["description"] for topic in body["topics"]))
                labels[language] = [topic["label"] for topic in body["topics"]]

                response = self.client.get("/api/cities", params={"language": language})
                self.assertEqual(response.status_code, 200, response.text)
                body = response.json()
                self.assertEqual(set(body), {"language", "cities"})
                self.assertEqual(body["language"], language)
                self.assertEqual(len(body["cities"]), 5)
                city_zones = {city["id"]: city["timezone"] for city in body["cities"]}
                self.assertEqual(city_zones["shanghai"], "Asia/Shanghai")
                self.assertEqual(city_zones["london"], "Europe/London")
                self.assertTrue(all(city["label"] for city in body["cities"]))
        self.assertNotEqual(labels["zh"], labels["en"])
        for call in calls:
            call.assert_not_called()
        self.wikipedia.assert_not_called()

    def test_chart_is_language_independent_and_has_no_other_business_effects(self):
        calls = self.forbid_business_calls("interpretation", "lots", "prepare_people", "recommend_people")
        responses = {}
        for language in LANGUAGES:
            with self.subTest(language=language):
                response = self.client.post("/api/chart", json=birth_payload(language))
                self.assertEqual(response.status_code, 200, response.text)
                body = response.json()
                responses[language] = body
                self.assertEqual(body["chart"], SAMPLE_CHART)
                self.assertEqual(body["language"], language)
                self.assertEqual(body["birth"]["timezone"], "Asia/Shanghai")
                self.assertEqual(body["birth"]["fold"], 0)
                self.assertEqual(
                    parse_datetime(body["birth"]["utc_datetime"]).isoformat(),
                    "2003-04-01T06:15:00+00:00"
                )
                self.assertEqual(
                    parse_datetime(body["birth"]["calculation_datetime"]).utcoffset(),
                    timedelta(hours=8)
                )
                self.assertFalse({"reading", "lot", "people"} & set(body))
        self.assertEqual(responses["en"]["element_labels"]["木"], "Wood")
        self.assertEqual(responses["zh"]["element_labels"]["木"], "木")
        for call in calls:
            call.assert_not_called()
        self.wikipedia.assert_not_called()

    def test_all_report_themes_in_both_languages_do_not_draw_or_query_people(self):
        calls = self.forbid_business_calls("lots", "prepare_people", "recommend_people")
        texts = {}
        for language in LANGUAGES:
            for topic in TOPICS:
                with self.subTest(language=language, topic=topic):
                    payload = {**birth_payload(language), "topic": topic}
                    response = self.client.post("/api/report", json=payload)
                    self.assertEqual(response.status_code, 200, response.text)
                    body = response.json()
                    self.assertEqual(body["chart"], SAMPLE_CHART)
                    self.assertFalse({"lot", "people"} & set(body))
                    reading = body["reading"]
                    self.assertEqual(reading["topic"], topic)
                    self.assertEqual(reading["dominant_elements"], ["木", "土"])
                    self.assertEqual(reading["missing_elements"], ["火"])
                    self.assertEqual([item["element"] for item in reading["items"]], ["木", "土"])
                    self.assertTrue(all(item["title"] and item["text"] and item["advice"] for item in reading["items"]))
                    for item in reading["items"]:
                        self.assertIn("3", item["basis"])
                        self.assertIn(body["element_labels"][item["element"]], item["basis"])
                    texts[language, topic] = reading["text"]
        for topic in TOPICS:
            self.assertNotEqual(texts["zh", topic], texts["en", topic])
        for call in calls:
            call.assert_not_called()
        self.wikipedia.assert_not_called()

    def test_report_defaults_remain_chinese_wealth(self):
        response = self.client.post("/api/report", json={"birth": SAMPLE_BIRTH})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["language"], "zh")
        self.assertEqual(response.json()["reading"]["topic"], "wealth")

    def test_draw_uses_each_theme_pool_without_birth_or_people(self):
        calls = self.forbid_business_calls("bazi", "interpretation", "prepare_people", "recommend_people")
        for language in LANGUAGES:
            rules = data_loader(language)
            for topic in TOPICS:
                with self.subTest(language=language, topic=topic):
                    response = self.client.post("/api/draw", json={"language": language, "topic": topic})
                    self.assertEqual(response.status_code, 200, response.text)
                    body = response.json()
                    self.assertEqual(set(body), {"language", "lot", "notice"})
                    lot = body["lot"]
                    self.assertEqual(lot["topic"], topic)
                    self.assertEqual(lot["topic_label"], rules["topics"][topic]["label"])
                    source = next(item for item in rules["topic_lots"][topic] if item["id"] == lot["id"])
                    for field in ("title", "text", "interpretation", "advice"):
                        self.assertEqual(lot[field], source[field])
        for call in calls:
            call.assert_not_called()
        self.wikipedia.assert_not_called()

    def test_people_works_without_a_prior_report_and_fetches_only_the_requested_matches(self):
        calls = self.forbid_business_calls("lots", "interpretation", "data_loader")
        self.wikipedia.side_effect = wikipedia_response
        full_results = {}
        for language in LANGUAGES:
            for limit in (1, 2, 3):
                with self.subTest(language=language, limit=limit):
                    self.wikipedia.reset_mock()
                    payload = {**birth_payload(language), "limit": limit}
                    response = self.client.post("/api/people", json=payload)
                    self.assertEqual(response.status_code, 200, response.text)
                    body = response.json()
                    self.assertEqual(body["dominant_elements"], ["木", "土"])
                    self.assertEqual(len(body["people"]), limit)
                    self.assertEqual(self.wikipedia.call_count, limit)
                    ranks = []
                    for match in body["people"]:
                        person = match["person"]
                        self.assertEqual(sum(person["element_counts"].values()), 8)
                        top = max(person["element_counts"].values())
                        expected_top = {key for key, value in person["element_counts"].items() if value == top}
                        self.assertEqual(set(person["dominant_elements"]), expected_top)
                        common = expected_top & {"木", "土"}
                        self.assertTrue(common)
                        self.assertEqual(set(match["common_elements"]), common)
                        self.assertEqual(match["same_dominant"], expected_top == {"木", "土"})
                        ranks.append((not match["same_dominant"], -len(common)))
                        self.assertTrue(match["biography"]["available"])
                        self.assertIn(f"({language})", match["biography"]["summary"])
                        self.assertTrue(match["biography"]["url"].startswith(f"https://{language}.wikipedia.org/"))
                        self.assertNotIn("error", match["biography"])
                        if language == "en":
                            self.assertEqual(person["name"], person["id"])
                    self.assertEqual(ranks, sorted(ranks))
                    for call in self.wikipedia.call_args_list:
                        request = call.args[0]
                        self.assertEqual(urlsplit(request.full_url).hostname, f"{language}.wikipedia.org")
                    if limit == 3:
                        full_results[language] = body["people"]
        self.assertEqual(
            [match["person"]["id"] for match in full_results["zh"]],
            [match["person"]["id"] for match in full_results["en"]]
        )
        for call in calls:
            call.assert_not_called()

    def test_people_network_failure_preserves_matches_and_hides_upstream_error(self):
        for language in LANGUAGES:
            with self.subTest(language=language):
                response = self.client.post("/api/people", json={**birth_payload(language), "limit": 1})
                self.assertEqual(response.status_code, 200, response.text)
                match = response.json()["people"][0]
                biography = match["biography"]
                self.assertFalse(biography["available"])
                self.assertTrue(biography["summary"])
                self.assertTrue(biography["url"].startswith(f"https://{language}.wikipedia.org/"))
                self.assertNotIn("error", biography)
                self.assertNotIn(UPSTREAM_ERROR, response.text)
                if language == "en":
                    self.assertIn("unavailable", biography["summary"].lower())

    def test_invalid_calendar_dates_times_and_unknown_zones_have_structured_errors(self):
        cases = (
            ({"date": "2023-02-29"}, "invalid_birth"),
            ({"date": "0000-01-01"}, "invalid_birth"),
            ({"time": "25:00"}, "invalid_birth"),
            ({"date": "2003-4-01"}, "invalid_request"),
            ({"time": "9:15"}, "invalid_request"),
            ({"timezone": "Not/A_Real_Zone"}, "invalid_timezone"),
            ({"timezone": "../etc/passwd"}, "invalid_timezone"),
            ({"date": "2999-01-01"}, "birth_in_future"),
            ({"date": "0001-01-01", "time": "00:00"}, "birth_out_of_range")
        )
        for changes, code in cases:
            with self.subTest(changes=changes):
                response = self.client.post("/api/chart", json=birth_payload("en", **changes))
                self.assert_error(response, code)

    def test_dst_gap_is_rejected_in_both_languages(self):
        messages = []
        for language in LANGUAGES:
            response = self.client.post("/api/chart", json=birth_payload(
                language, date="2024-03-31", time="01:30", timezone="Europe/London"
            ))
            messages.append(self.assert_error(response, "time_nonexistent")["message"])
        self.assertNotEqual(*messages)

    def test_ambiguous_clock_time_returns_fold_candidates(self):
        response = self.client.post("/api/chart", json=birth_payload(
            "en", date="2024-10-27", time="01:30", timezone="Europe/London"
        ))
        error = self.assert_error(response, "time_ambiguous")
        candidates = error["details"]["candidates"]
        self.assertEqual([item["fold"] for item in candidates], [0, 1])
        moments = [parse_datetime(item["utc_datetime"]) for item in candidates]
        self.assertEqual(moments[1] - moments[0], timedelta(hours=1))
        local_times = [parse_datetime(item["local_datetime"]) for item in candidates]
        self.assertEqual(local_times[0].replace(tzinfo=None), local_times[1].replace(tzinfo=None))
        self.assertNotEqual(local_times[0].utcoffset(), local_times[1].utcoffset())

    def test_fold_zero_and_one_resolve_to_different_instants_and_charts(self):
        results = []
        for fold in (0, 1):
            response = self.client.post("/api/chart", json=birth_payload(
                "en", date="2024-10-27", time="01:30", timezone="Europe/London", fold=fold
            ))
            self.assertEqual(response.status_code, 200, response.text)
            body = response.json()
            self.assertEqual(body["birth"]["fold"], fold)
            results.append(body)
        first = parse_datetime(results[0]["birth"]["utc_datetime"])
        second = parse_datetime(results[1]["birth"]["utc_datetime"])
        self.assertEqual(second - first, timedelta(hours=1))
        self.assertNotEqual(results[0]["chart"]["pillars"]["time"], results[1]["chart"]["pillars"]["time"])

    def test_second_fold_is_rejected_for_an_unambiguous_clock_time(self):
        response = self.client.post("/api/chart", json=birth_payload("en", fold=1))
        self.assert_error(response, "invalid_fold")

    def test_fold_requires_an_integer_zero_or_one(self):
        for fold in (True, False, "0", "1", 0.0, 1.0, -1, 2):
            with self.subTest(fold=fold, value_type=type(fold).__name__):
                response = self.client.post("/api/chart", json=birth_payload("en", fold=fold))
                self.assert_error(response, "invalid_request")

    def test_people_limit_rejects_coercion_and_values_outside_one_to_three(self):
        calls = self.forbid_business_calls("bazi", "prepare_people", "recommend_people")
        for limit in (0, -1, 4, True, False, 1.0, "2", None):
            with self.subTest(limit=limit, value_type=type(limit).__name__):
                response = self.client.post("/api/people", json={**birth_payload("en"), "limit": limit})
                self.assert_error(response, "invalid_request")
        for call in calls:
            call.assert_not_called()

    def test_unknown_languages_and_topics_are_rejected(self):
        for endpoint in ("chart", "report", "draw", "people"):
            for language in ("fr", "EN", "", True, 1, None):
                with self.subTest(endpoint=endpoint, language=language):
                    payload = {"language": language}
                    if endpoint != "draw":
                        payload["birth"] = SAMPLE_BIRTH
                    self.assert_error(self.client.post(f"/api/{endpoint}", json=payload), "invalid_request")
        for endpoint in ("topics", "cities"):
            self.assert_error(self.client.get(f"/api/{endpoint}", params={"language": "fr"}), "invalid_request")
        for endpoint in ("report", "draw"):
            payload = {"language": "en", "topic": "unknown"}
            if endpoint == "report":
                payload["birth"] = SAMPLE_BIRTH
            self.assert_error(self.client.post(f"/api/{endpoint}", json=payload), "invalid_request")

    def test_extra_json_fields_are_rejected_including_nested_birth_fields(self):
        for endpoint in ("chart", "report", "draw", "people"):
            with self.subTest(endpoint=endpoint):
                payload = {"language": "en", "unexpected": "do not silently ignore this"}
                if endpoint != "draw":
                    payload["birth"] = SAMPLE_BIRTH
                error = self.assert_error(self.client.post(f"/api/{endpoint}", json=payload), "invalid_request")
                self.assertTrue(any(item["field"].endswith("unexpected") for item in error["details"]))
        payload = birth_payload("en", unexpected="nested field")
        error = self.assert_error(self.client.post("/api/chart", json=payload), "invalid_request")
        self.assertTrue(any(item["field"].endswith("birth.unexpected") for item in error["details"]))
        self.assert_error(self.client.post("/api/draw", json=birth_payload("en")), "invalid_request")

    def test_malformed_json_missing_fields_and_unknown_routes_share_error_shape(self):
        self.assert_error(self.client.post(
            "/api/chart?language=en", content='{"birth":', headers={"Content-Type": "application/json"}
        ), "invalid_request")
        payload = birth_payload("en")
        del payload["birth"]["date"]
        self.assert_error(self.client.post("/api/chart", json=payload), "invalid_request")
        self.assert_error(self.client.get("/api/not-found?language=en"), "not_found", 404)
        response = self.client.get("/api/people?language=en")
        self.assert_error(response, "method_not_allowed", 405)
        self.assertIn("POST", response.headers.get("allow", ""))

    def test_rule_file_failure_returns_503_without_leaking_details(self):
        with patch.object(api_module, "data_loader", side_effect=OSError(UPSTREAM_ERROR)):
            messages = {}
            for language in LANGUAGES:
                for endpoint in ("topics", "report", "draw"):
                    with self.subTest(language=language, endpoint=endpoint):
                        if endpoint == "topics":
                            response = self.client.get("/api/topics", params={"language": language})
                        else:
                            payload = {"language": language, "topic": "study"}
                            if endpoint == "report":
                                payload["birth"] = deepcopy(SAMPLE_BIRTH)
                            response = self.client.post(f"/api/{endpoint}", json=payload)
                        error = self.assert_error(response, "rules_unavailable", 503)
                        messages[language] = error["message"]
                        self.assertNotIn(UPSTREAM_ERROR, response.text)
            self.assertNotEqual(messages["zh"], messages["en"])
            response = self.client.post("/api/chart", json=birth_payload("en"))
            self.assertEqual(response.status_code, 200, response.text)

    def test_unexpected_failure_is_localized_and_does_not_return_a_traceback(self):
        messages = []
        configured = os.getenv("SUANMING_CORS_ORIGINS", "http://localhost:5173")
        origin = next((item.strip() for item in configured.split(",") if item.strip()), None)
        headers = {"Origin": origin} if origin is not None else {}
        with patch.object(api_module, "bazi", side_effect=RuntimeError(UPSTREAM_ERROR)):
            with self.assertLogs(api_module.__name__, level="ERROR"):
                for language in LANGUAGES:
                    response = self.client.post("/api/chart", json=birth_payload(language), headers=headers)
                    error = self.assert_error(response, "internal_error", 500)
                    messages.append(error["message"])
                    self.assertNotIn(UPSTREAM_ERROR, response.text)
                    if language == "en":
                        self.assertTrue(error["message"].isascii())
                    if origin is not None:
                        self.assertEqual(response.headers.get("access-control-allow-origin"), origin)
        self.assertNotEqual(*messages)

    def test_cors_allows_configured_frontend_origin_and_post_preflight(self):
        configured = os.getenv("SUANMING_CORS_ORIGINS", "http://localhost:5173")
        origin = next((item.strip() for item in configured.split(",") if item.strip()), None)
        if origin is None:
            self.skipTest("CORS origins are explicitly disabled in this environment")
        response = self.client.get("/api/health", headers={"Origin": origin})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.headers.get("access-control-allow-origin"), origin)
        self.assertNotEqual(response.headers.get("access-control-allow-credentials"), "true")
        response = self.client.options("/api/report", headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type"
        })
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.headers.get("access-control-allow-origin"), origin)
        self.assertIn("POST", response.headers.get("access-control-allow-methods", ""))
        self.assertIn("content-type", response.headers.get("access-control-allow-headers", "").lower())

    def test_cors_does_not_grant_access_to_an_unlisted_origin(self):
        origin = "https://not-a-configured-frontend.invalid"
        configured = {item.strip() for item in os.getenv("SUANMING_CORS_ORIGINS", "").split(",")}
        if origin in configured:
            self.skipTest("The test origin was explicitly configured as allowed")
        response = self.client.get("/api/health", headers={"Origin": origin})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertNotIn("access-control-allow-origin", response.headers)
        response = self.client.options("/api/report", headers={
            "Origin": origin, "Access-Control-Request-Method": "POST"
        })
        self.assertEqual(response.status_code, 400, response.text)
        self.assertNotIn("access-control-allow-origin", response.headers)


if __name__ == "__main__":
    unittest.main()
