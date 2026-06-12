import logging

from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool

from .sub_agents import bigquery_agent, transaction_agent

logger = logging.getLogger(__name__)


async def call_bigquery_agent(
    question: str,
    tool_context: ToolContext,
):
    """Tool to call bigquery database (nl2sql) agent."""
    logger.debug("call_bigquery_agent: %s", question)

    agent_tool = AgentTool(agent=bigquery_agent)

    bigquery_agent_output = await agent_tool.run_async(
        args={"request": question}, tool_context=tool_context
    )
    tool_context.state["bigquery_agent_output"] = bigquery_agent_output
    return bigquery_agent_output


async def call_transaction_agent(
    question: str,
    tool_context: ToolContext,
):
    """Tool to call transaction agent."""
    logger.debug("call_transaction_agent: %s", question)

    agent_tool = AgentTool(agent=transaction_agent)

    transaction_agent_output = await agent_tool.run_async(
        args={"request": question}, tool_context=tool_context
    )
    tool_context.state["transaction_agent_output"] = transaction_agent_output
    return transaction_agent_output