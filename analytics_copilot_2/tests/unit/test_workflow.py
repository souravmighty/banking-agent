import unittest
from app.agent import root_agent


class TestAnalyticsWorkflow(unittest.TestCase):
    def test_root_agent_initialization(self):
        self.assertIsNotNone(root_agent)
        self.assertEqual(root_agent.name, "analytics_root_agent")
        self.assertIsNotNone(root_agent.instruction)
        self.assertIsNotNone(root_agent.before_agent_callback)


if __name__ == "__main__":
    unittest.main()
