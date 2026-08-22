import json
import unittest

from app.sub_agents.visualization.agent import visualization_agent
from app.sub_agents.visualization.prompts import return_instructions_visualization
from app.sub_agents.visualization.tools import validate_vega_lite_spec


class TestVisualizationAgent(unittest.TestCase):
    def test_prompt_instructions(self):
        prompt = return_instructions_visualization()
        self.assertIn("Vega-Lite", prompt)
        self.assertIn("values", prompt)

    def test_validate_vega_lite_spec_valid(self):
        valid_spec = json.dumps({
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "description": "Monthly Trend",
            "data": {
                "values": [
                    {"month": "2026-01", "acquisitions": 150},
                    {"month": "2026-02", "acquisitions": 210},
                ]
            },
            "mark": "line",
            "encoding": {
                "x": {"field": "month", "type": "temporal"},
                "y": {"field": "acquisitions", "type": "quantitative"},
            },
        })

        result = validate_vega_lite_spec(valid_spec)
        self.assertEqual(result["status"], "VALID")
        self.assertEqual(result["mark"], "line")
        self.assertEqual(result["data_record_count"], 2)

    def test_validate_vega_lite_spec_with_code_fence(self):
        fenced_spec = """```vega-lite
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "data": {
    "values": [{"category": "Retail", "volume": 5000}]
  },
  "mark": "bar",
  "encoding": {
    "x": {"field": "category", "type": "nominal"},
    "y": {"field": "volume", "type": "quantitative"}
  }
}
```"""
        result = validate_vega_lite_spec(fenced_spec)
        self.assertEqual(result["status"], "VALID")
        self.assertEqual(result["mark"], "bar")

    def test_validate_vega_lite_spec_invalid_json(self):
        invalid_spec = "{ bad json "
        result = validate_vega_lite_spec(invalid_spec)
        self.assertEqual(result["status"], "INVALID")
        self.assertIn("JSON syntax error", result["error"])

    def test_validate_vega_lite_spec_missing_mark(self):
        spec_no_mark = json.dumps({
            "data": {"values": [{"a": 1}]}
        })
        result = validate_vega_lite_spec(spec_no_mark)
        self.assertEqual(result["status"], "INVALID")
        self.assertTrue(any("mark" in err for err in result.get("errors", [])))

    def test_agent_structure(self):
        self.assertEqual(visualization_agent.name, "visualization_agent")
        self.assertEqual(len(visualization_agent.tools), 1)


if __name__ == "__main__":
    unittest.main()
