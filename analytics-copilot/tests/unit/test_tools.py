import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from app.tools import call_bigquery_agent, call_visualization_agent


class TestAnalyticsTools(unittest.IsolatedAsyncioTestCase):
    async def test_call_bigquery_agent_structure(self):
        tool_context = AsyncMock()
        tool_context.state = {
            "database_settings": {"bigquery": {"schema": {}}},
        }

        with patch("app.sub_agents.bigquery.tools.bigquery_nl2sql") as mock_nl2sql, \
             patch("app.sub_agents.bigquery.tools.execute_bigquery_sql") as mock_exec:
            mock_nl2sql.return_value = "SELECT 1"
            mock_exec.return_value = [{"col": 1}]

            res = await call_bigquery_agent("Test question", tool_context)
            self.assertEqual(res["sql"], "SELECT 1")
            self.assertEqual(res["sql_results"], [{"col": 1}])
            self.assertEqual(tool_context.state["sql_query"], "SELECT 1")
            self.assertEqual(tool_context.state["bigquery_query_result"], [{"col": 1}])

    async def test_call_visualization_agent_structure(self):
        tool_context = AsyncMock()
        tool_context.state = {}

        with patch("app.tools.AgentTool") as mock_agent_tool_cls:
            mock_tool_instance = AsyncMock()
            mock_tool_instance.run_async.return_value = "```vega-lite\n{}\n```"
            mock_agent_tool_cls.return_value = mock_tool_instance

            res = await call_visualization_agent(
                "Trend chart",
                '[{"month": "2026-01", "val": 10}]',
                tool_context,
            )
            self.assertIn("vega-lite", res)
            self.assertEqual(
                tool_context.state["visualization_agent_output"],
                "```vega-lite\n{}\n```",
            )

    async def test_retrieve_analytical_business_knowledge_success(self):
        from app.tools import retrieve_analytical_business_knowledge

        tool_context = AsyncMock()
        tool_context.state = {"firebase_id_token": "mock_jwt_token"}

        mock_response_data = {
            "query": "What is the formula for Customer Churn Rate?",
            "results": [
                {
                    "document_id": "doc_staff_kpi",
                    "document_name": "Staff KPI & Metrics Definitions",
                    "logical_document_id": "doc-kpi-metrics",
                    "version": "v1.0.0",
                    "access_control": ["STAFF"],
                    "text": "Churn Rate is calculated as (Lost Customers / Starting Customers) * 100 over a 30-day window.",
                    "source_uri": "gs://banking-agent-knowledge-docs/kpis/metrics.pdf",
                    "relevance_score": 0.94,
                }
            ],
            "total_found": 1,
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response_data
            mock_post.return_value = mock_resp

            res = await retrieve_analytical_business_knowledge(
                query="What is the formula for Customer Churn Rate?",
                tool_context=tool_context,
            )

            self.assertEqual(res["total_found"], 1)
            self.assertEqual(res["results"][0]["document_id"], "doc_staff_kpi")
            self.assertIn("STAFF", res["results"][0]["access_control"])

            # Verify that STAFF access_scope was sent in the payload
            call_kwargs = mock_post.call_args[1]
            self.assertEqual(call_kwargs["json"]["access_scope"], "STAFF")


if __name__ == "__main__":
    unittest.main()

