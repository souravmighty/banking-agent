# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import contextlib
import os
import uuid
from collections.abc import AsyncIterator
from typing import Literal

from a2a.server.tasks import InMemoryTaskStore
from dotenv import load_dotenv
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app
from google.adk.cli.utils.agent_loader import AgentLoader
from google.adk.runners import Runner
from pydantic import BaseModel, Field

from app.app_utils import services
from app.app_utils.a2a import attach_a2a_routes
from app.app_utils.reasoning_engine_adapter import attach_reasoning_engine_routes

load_dotenv()
allow_origins = (
    os.getenv("ALLOW_ORIGINS", "").split(",") if os.getenv("ALLOW_ORIGINS") else None
)

AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    from app.agent import app as adk_app
    from app.agent import root_agent

    runner = Runner(
        app=adk_app,
        session_service=services.get_session_service(),
        artifact_service=services.get_artifact_service(),
        auto_create_session=True,
    )
    app.state.runner = runner
    app.state.agent_app_name = adk_app.name
    await attach_a2a_routes(
        app,
        agent=root_agent,
        runner=runner,
        task_store=InMemoryTaskStore(),
        rpc_path=f"/a2a/{adk_app.name}",
    )
    yield


class AnalyticsCopilotAgentLoader(AgentLoader):
    """Agent loader that ensures analytics-copilot, analytics_copilot, and app names resolve."""

    def list_agents(self) -> list[str]:
        return ["analytics-copilot", "analytics_copilot", "analytics_copilot_2", "app"]

    def _perform_load(self, agent_name: str):
        if agent_name in (
            "analytics-copilot",
            "analytics_copilot",
            "analytics_copilot_2",
            "app",
        ):
            from app.agent import app as adk_app

            return adk_app
        return super()._perform_load(agent_name)


class Feedback(BaseModel):
    """Represents user feedback for conversation evaluation."""

    score: int | float
    text: str | None = ""
    log_type: Literal["feedback"] = "feedback"
    service_name: Literal["analytics-copilot"] = "analytics-copilot"
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


agent_loader = AnalyticsCopilotAgentLoader(AGENT_DIR)

app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    agent_loader=agent_loader,
    web=True,
    artifact_service_uri=services.ARTIFACT_SERVICE_URI,
    allow_origins=allow_origins,
    session_service_uri=services.SESSION_SERVICE_URI,
    otel_to_cloud=os.getenv("OTEL_TO_CLOUD", "false").lower() == "true",
    lifespan=lifespan,
)
app.title = "analytics-copilot"
app.description = "API for interacting with the Agent analytics-copilot"
attach_reasoning_engine_routes(app)


@app.post("/feedback")
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    """Collect and log user feedback to Cloud Logging / BigQuery sink."""
    try:
        from google.cloud import logging as google_cloud_logging

        logging_client = google_cloud_logging.Client()
        cloud_logger = logging_client.logger("analytics-copilot-feedback")
        cloud_logger.log_struct(feedback.model_dump(), severity="INFO")
    except Exception:
        import logging

        logging.getLogger("feedback").info(
            "User feedback received: %s", feedback.model_dump_json()
        )

    return {"status": "success"}


# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
