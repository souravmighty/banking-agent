import asyncio
import logging

from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool

try:
    from .sub_agents import bigquery_agent, visualization_agent
except (ImportError, ValueError):
    from app.sub_agents import bigquery_agent, visualization_agent

logger = logging.getLogger(__name__)

# Maximum concurrent BigQuery agent sub-tasks per turn
MAX_CONCURRENT_BIGQUERY_CALLS = 5
_bigquery_semaphore = asyncio.Semaphore(MAX_CONCURRENT_BIGQUERY_CALLS)


async def call_bigquery_agent(
    question: str,
    tool_context: ToolContext,
):
    """Tool to call BigQuery analytical agent (NL2SQL and query execution).

    Each invocation must contain a single, focused analytical question. If the user
    inquiry contains multiple distinct questions or metrics, invoke this tool multiple
    times in parallel with discrete, self-contained questions (up to a maximum of 5 concurrent calls).

    Args:
        question: A single, focused natural language business analytics question with required filters, metrics, and timeframes.
    """
    logger.debug("call_bigquery_agent: %s", question)

    async with _bigquery_semaphore:
        agent_tool = AgentTool(agent=bigquery_agent)

        bigquery_agent_output = None
        last_exception = None

        # Robust execution with up to 2 retries for transient transport/auth network glitches
        for attempt in range(2):
            try:
                bigquery_agent_output = await agent_tool.run_async(
                    args={"request": question}, tool_context=tool_context
                )
                break
            except Exception as exc:
                last_exception = exc
                logger.warning(
                    "call_bigquery_agent attempt %d failed with error: %s. Retrying...",
                    attempt + 1,
                    exc,
                )
                if attempt == 0:
                    await asyncio.sleep(1.0)

        if bigquery_agent_output is None:
            error_msg = (
                f"Network or authentication connectivity issue: {last_exception}"
            )
            logger.error("call_bigquery_agent failed completely: %s", error_msg)
            bigquery_agent_output = {
                "explain": f"Encountered temporary transport/connectivity error: {last_exception}",
                "sql": "",
                "sql_results": [],
                "nl_results": f"Unable to reach the BigQuery analytical service due to a transient connection error ({last_exception}). Please retry your request.",
            }

        # Maintain both a collection list (for multi-query parallel runs) and latest output key
        if "bigquery_agent_outputs" not in tool_context.state:
            tool_context.state["bigquery_agent_outputs"] = []
        tool_context.state["bigquery_agent_outputs"].append(
            {
                "question": question,
                "output": bigquery_agent_output,
            }
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

    visualization_output = None
    last_exception = None

    for attempt in range(2):
        try:
            visualization_output = await agent_tool.run_async(
                args={"request": request_prompt}, tool_context=tool_context
            )
            break
        except Exception as exc:
            last_exception = exc
            logger.warning(
                "call_visualization_agent attempt %d failed with error: %s. Retrying...",
                attempt + 1,
                exc,
            )
            if attempt == 0:
                await asyncio.sleep(1.0)

    if visualization_output is None:
        logger.error("call_visualization_agent failed: %s", last_exception)
        visualization_output = f"Unable to generate chart specification due to temporary connectivity issue: {last_exception}"

    # Maintain collection list and latest output key
    if "visualization_agent_outputs" not in tool_context.state:
        tool_context.state["visualization_agent_outputs"] = []
    tool_context.state["visualization_agent_outputs"].append(
        {
            "analytical_goal": analytical_goal,
            "output": visualization_output,
        }
    )
    tool_context.state["visualization_agent_output"] = visualization_output

    return visualization_output
