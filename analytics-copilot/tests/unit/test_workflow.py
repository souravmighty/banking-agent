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

import pytest
from app.agent import root_agent, app
from app.schemas import HypothesisTask, HypothesisPlan, AnalyticsSynthesis, RankedHypothesis


def test_workflow_structure():
    assert root_agent.name == "analytics_copilot"
    assert len(root_agent.edges) == 3
    assert app.name == "app"


def test_schema_validations():
    task = HypothesisTask(
        id="H1",
        title="Payment Surge",
        rationale="Higher payoffs in Q2",
        base_filters="status='Active'",
        target_metric="payoff_rate",
        sql_intent="Query monthly payoff rate by segment",
    )
    assert task.id == "H1"

    plan = HypothesisPlan(
        business_question="Why did balances drop?",
        common_base_cohort="status='Active'",
        hypotheses=[task],
    )
    assert len(plan.hypotheses) == 1

    synth = AnalyticsSynthesis(
        executive_summary="Summary",
        ranked_hypotheses=[
            RankedHypothesis(
                rank=1,
                hypothesis_id="H1",
                title="Payment Surge",
                verdict="CONFIRMED",
                estimated_impact="High",
                summary="Payoff rate jumped",
            )
        ],
        sufficiency_verdict="SUFFICIENT",
        recommended_next_steps=["Drill down into Prime"],
        narrative_report="# Report",
    )
    assert synth.sufficiency_verdict == "SUFFICIENT"
