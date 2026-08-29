import unittest
from unittest.mock import AsyncMock, patch

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


if __name__ == "__main__":
    unittest.main()
