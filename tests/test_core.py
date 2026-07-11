import sys
import json
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fastapi.testclient import TestClient

import main
import llm.client as llm_client
from llm.client import parse_json_response
from query.schema import AggregateSpec, OrderSpec, QueryPlan, TABLE_ORDERS
from query.sql import build_sql
from session import SessionStore


class LLMJsonParsingTests(unittest.TestCase):
    def test_parse_json_response_accepts_fenced_json(self):
        payload = parse_json_response('```json\n{"query_type": "single"}\n```')

        self.assertEqual(payload["query_type"], "single")

    def test_parse_json_response_extracts_object_from_text(self):
        payload = parse_json_response('计划如下：{"query_type": "aggregate"} 请执行。')

        self.assertEqual(payload["query_type"], "aggregate")

    def test_parse_json_response_rejects_invalid_json(self):
        with self.assertRaisesRegex(ValueError, "有效 JSON"):
            parse_json_response("not-json")


class SessionStoreTests(unittest.TestCase):
    def test_format_messages_uses_passed_history(self):
        history = [{"role": "user", "content": "查 GMV"}, {"role": "assistant", "content": "好的"}]

        self.assertEqual(SessionStore.format_messages(history), "user: 查 GMV\nassistant: 好的")

    def test_format_messages_handles_empty_history(self):
        self.assertEqual(SessionStore.format_messages([]), "（无历史对话）")


class SQLBuilderTests(unittest.TestCase):
    def test_aggregate_order_by_allows_alias(self):
        columns = {"orders": {"province", "total_amount"}}
        with (
            patch("query.schema.load_columns", return_value=columns),
            patch("query.sql.load_columns", return_value=columns),
            patch("query.sql.check_field", return_value=None),
        ):
            plan = QueryPlan(
                query_type="aggregate",
                table_name=TABLE_ORDERS,
                primary_table=TABLE_ORDERS,
                group_by=["province"],
                aggregates=[AggregateSpec(field="total_amount", func="sum", alias="gmv")],
                order_by=[OrderSpec(field="gmv", direction="desc")],
            )
            sql, params = build_sql(plan)

        self.assertIn("SUM(`t0`.`total_amount`) AS `gmv`", sql)
        self.assertIn("ORDER BY `gmv` DESC", sql)
        self.assertEqual(params, [100])


class HealthEndpointTests(unittest.TestCase):
    def test_health_reports_warning_when_llm_key_missing(self):
        with patch.object(main, "LLM_API_KEY", ""), patch.object(
            main,
            "check_database_health",
            return_value={"status": "ok", "message": "db ok"},
        ):
            response = TestClient(main.app).get("/health")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "warning")
        self.assertEqual(body["database"]["status"], "ok")
        self.assertEqual(body["llm"]["status"], "warning")


class DemoModeTests(unittest.TestCase):
    def test_demo_mode_returns_deterministic_intent(self):
        with patch.object(llm_client, "DEMO_MODE", True):
            payload = json.loads(
                llm_client.run_llm_cfg(
                    "intent_analysis_llm_cfg",
                    user_question="各省份订单金额排名",
                )
            )

        self.assertEqual(payload["query_type"], "aggregate")
        self.assertEqual(payload["aggregates"][0]["alias"], "gmv")

    def test_demo_scenarios_endpoint_exposes_fixed_cases(self):
        response = TestClient(main.app).get("/demo-scenarios")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["scenarios"]), 4)


class ApiKeyTests(unittest.TestCase):
    def test_protected_endpoint_requires_api_key_when_enabled(self):
        with patch.object(main, "API_KEY", "demo-secret"):
            response = TestClient(main.app).get("/tables")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"]["code"], "UNAUTHORIZED")


class RunEndpointTests(unittest.TestCase):
    def test_run_returns_demo_metadata(self):
        class FakeGraph:
            async def ainvoke(self, payload):
                return {
                    "final_answer": "演示结果",
                    "chart_url": None,
                    "query_plan": {"query_type": "aggregate"},
                    "query_result": [{"record_id": "1", "fields": {"gmv": 100}}],
                }

        with patch.object(main, "main_graph", FakeGraph()):
            response = TestClient(main.app).post(
                "/run",
                json={"user_question": "订单 GMV", "session_id": "demo"},
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["final_answer"], "演示结果")
        self.assertEqual(body["query_plan"]["query_type"], "aggregate")
        self.assertEqual(body["rows"][0]["fields"]["gmv"], 100)
        self.assertGreaterEqual(body["execution_ms"], 0)
        self.assertTrue(body["request_id"])


if __name__ == "__main__":
    unittest.main()
