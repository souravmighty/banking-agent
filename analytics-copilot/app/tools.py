import asyncio
import logging

from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool

try:
    from .sub_agents import bigquery_agent, visualization_agent
except (ImportError, ValueError):
    from app.sub_agents import bigquery_agent, visualization_agent

logger = logging.getLogger(__name__)

# Maximum concurrent BigQuery and Visualization agent sub-tasks per turn
MAX_CONCURRENT_BIGQUERY_CALLS = 5
_bigquery_semaphore = asyncio.Semaphore(MAX_CONCURRENT_BIGQUERY_CALLS)

MAX_CONCURRENT_VISUALIZATION_CALLS = 2
_visualization_semaphore = asyncio.Semaphore(MAX_CONCURRENT_VISUALIZATION_CALLS)


async def call_bigquery_agent(
    question: str,
    tool_context: ToolContext,
):
    """Tool to call BigQuery analytical agent (NL2SQL and query execution).

    Each invocation must contain a focused analytical question. If the user
    inquiry contains multiple distinct questions or metrics, invoke this tool multiple
    times in parallel with discrete, self-contained questions (up to a maximum of 5 concurrent calls).

    Args:
        question: A focused natural language business analytics question with required filters, metrics, and timeframes.
    """
    logger.debug("call_bigquery_agent: %s", question)

    async with _bigquery_semaphore:
        # 1. Ensure database settings are loaded in context state
        if "database_settings" not in tool_context.state:
            try:
                from .agent import load_analytics_metadata_in_context
            except (ImportError, ValueError):
                from app.agent import load_analytics_metadata_in_context
            load_analytics_metadata_in_context(tool_context)

        # 2. Import direct NL2SQL and execution tools
        try:
            from .sub_agents.bigquery.tools import (
                bigquery_nl2sql,
                execute_bigquery_sql,
            )
        except (ImportError, ValueError):
            from app.sub_agents.bigquery.tools import (
                bigquery_nl2sql,
                execute_bigquery_sql,
            )

        sql = ""
        rows = []
        error_msg = None

        # Attempt 1: Fast path with pruned schema
        try:
            sql = bigquery_nl2sql(question=question, tool_context=tool_context)
            rows = await asyncio.to_thread(execute_bigquery_sql, sql)
        except Exception as exc:
            logger.warning(
                "call_bigquery_agent direct execution failed: %s. Retrying with full schema...",
                exc,
            )
            error_msg = str(exc)

            # Attempt 2: Fallback retry with full schema & error feedback
            try:
                tool_context.state["force_full_schema"] = True
                retry_question = (
                    f"{question}\n\n[EXECUTION ERROR CORRECTION]\n"
                    f"Previous attempt generated SQL:\n{sql}\n"
                    f"BigQuery execution error:\n{exc}\n"
                    f"Please correct table names, column references, or syntax and provide valid BigQuery SQL."
                )
                sql = bigquery_nl2sql(
                    question=retry_question, tool_context=tool_context
                )
                rows = await asyncio.to_thread(execute_bigquery_sql, sql)
                error_msg = None
            except Exception as retry_exc:
                logger.error("call_bigquery_agent retry failed: %s", retry_exc)
                error_msg = str(retry_exc)
            finally:
                tool_context.state["force_full_schema"] = False

        if error_msg:
            bigquery_agent_output = {
                "explain": f"Encountered BigQuery execution error: {error_msg}",
                "sql": sql,
                "sql_results": [],
                "nl_results": f"Unable to retrieve records from BigQuery due to: {error_msg}",
            }
        else:
            bigquery_agent_output = {
                "explain": f"Generated and executed BigQuery SQL for: {question}",
                "sql": sql,
                "sql_results": rows,
                "nl_results": f"Successfully retrieved {len(rows)} rows from BigQuery.",
            }

        # Store in state for visualization / context
        tool_context.state["bigquery_query_result"] = rows
        tool_context.state["sql_query"] = sql

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

    Limit chart generation to at most 2 charts per turn. If multiple charts are needed, invoke this tool
    concurrently in parallel in a single turn.

    Args:
        analytical_goal: Description of what chart is needed (e.g. 'Month-on-month acquisition trend line chart' or 'Deposit balance distribution by segment bar chart').
        data_summary_or_records: The raw query result rows, JSON records, or formatted data table produced by the BigQuery agent.
    """
    logger.debug("call_visualization_agent: %s", analytical_goal)

    async with _visualization_semaphore:
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
