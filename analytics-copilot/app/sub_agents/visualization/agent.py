"""Visualization Agent: generates interactive Vega-Lite v5 chart specifications."""

import logging
import os

import google.genai.types as genai_types
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.planners import BuiltInPlanner

from .prompts import return_instructions_visualization
from .tools import validate_vega_lite_spec

load_dotenv()

logger = logging.getLogger(__name__)

visualization_agent = LlmAgent(
    model=os.getenv("VISUALIZATION_AGENT_MODEL", "gemini-3.7-flash"),
    name="visualization_agent",
    planner=BuiltInPlanner(
        thinking_config=genai_types.ThinkingConfig(thinking_budget=0)
    ),
    instruction=return_instructions_visualization(),
    tools=[validate_vega_lite_spec],
    generate_content_config=genai_types.GenerateContentConfig(temperature=0.01),
)
