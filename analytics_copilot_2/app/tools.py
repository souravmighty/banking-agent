import logging
from typing import Optional

from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool

try:
    from .sub_agents import bigquery_agent, visualization_agent
except (ImportError, ValueError):
    from app.sub_agents import bigquery_agent, visualization_agent

logger = logging.getLogger(__name__)


async def call_bigquery_agent(
    question: str,
    tool_context: ToolContext,
):
    """Tool to call BigQuery analytical agent (NL2SQL and query execution)."""
    logger.debug("call_bigquery_agent: %s", question)

    agent_tool = AgentTool(agent=bigquery_agent)

    bigquery_agent_output = await agent_tool.run_async(
        args={"request": question}, tool_context=tool_context
    )
    tool_context.state["bigquery_agent_output"] = bigquery_agent_output
    return bigquery_agent_output


async def call_visualization_agent(
    analytical_goal: str,
    data_summary_or_records: str,
    tool_context: ToolContext,
) -> str:
    """Tool to call the BI Visualization Agent to generate a self-contained Vega-Lite v5 chart specification.

    Args:
        analytical_goal: Description of what chart is needed (e.g. 'Month-on-month acquisition trend line chart' or 'Deposit balance distribution by segment bar chart').
        data_summary_or_records: The raw query result rows, JSON records, or formatted data table produced by the BigQuery agent.
    """
    logger.debug("call_visualization_agent: %s", analytical_goal)

    agent_tool = AgentTool(agent=visualization_agent)
    request_prompt = (
        f"Analytical Goal: {analytical_goal}\n\n"
        f"Data Records / Table:\n{data_summary_or_records}"
    )

    visualization_output = await agent_tool.run_async(
        args={"request": request_prompt}, tool_context=tool_context
    )
    tool_context.state["visualization_agent_output"] = visualization_output
    return visualization_output