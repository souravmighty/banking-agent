import os
import sys
import json
import logging
import asyncio
from types import SimpleNamespace

# Set environment variables for end-to-end test
os.environ["CUSTOMER_IDENTITY_SERVICE_URL"] = "http://localhost:8001"
os.environ["IDENTITY_SERVICE_URL"] = "http://localhost:8001"

JWT_TOKEN = (
    "eyJhbGciOiJSUzI1NiIsImtpZCI6IjZhYzkwNDdmNjcxMmZjZDVjZjY3YTMzMDc5NDFkOWZhNDIyODM5NTUiLCJ0eXAiOiJKV1QifQ."
    "eyJuYW1lIjoiU291cmF2IE1haXRpIiwicGljdHVyZSI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hL0FDZzhvY0w2NV9hQlZJb2EwUTVQUm1YanRYN3NPRldGOVNhS0FSUDQ1Rm1OYkl2UFBPQkpDVWd4Ync9czk2LWMiLCJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vYmFua2luZy1hZ2VudC1yYWctbWNwIiwiYXVkIjoiYmFua2luZy1hZ2VudC1yYWctbWNwIiwiYXV0aF90aW1lIjoxNzg3MjUzNDEyLCJ1c2VyX2lkIjoiVUJCSGFUa2dOdVZEM0xiUDVudjR5d09xNjh2MiIsInN1YiI6IlVCQkhhVGtnTnVWRDNMYlA1bnY0eXdPcTY4djIiLCJpYXQiOjE3ODcyNTM0MTIsImV4cCI6MTc4NzI1NzAxMiwiZW1haWwiOiJzb3VyYXZtYWl0aTE5OTdAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZpcmViYXNlIjp7ImlkZW50aXRpZXMiOnsiZ29vZ2xlLmNvbSI6WyIxMTA2MjU3MjY2MzY5NDc2OTI1NzIiXSwiZW1haWwiOlsic291cmF2bWFpdGkxOTk3QGdtYWlsLmNvbSJdfSwic2lnbl9pbl9wcm92aWRlciI6Imdvb2dsZS5jb20ifX0."
    "jvgLdvlteDUP6TsvgqUl6PMls7w44V0G8_lfKwC2f8TS-9NblD6NrEc3E3ltiyIhM58f_LnEjPt6zQH-yoymIgJClE1MAHtmMb0QN1MNxywcfxUmGQZlUROSujV1W3ai5ka4tKMFlTnwMvSkOnM60QDmMdhOBz5i61wCl7MvxtBcotfZvdBjN3UdC-EWdKPBnhyQnC7XNoz7M0cpr8QmYnmhwKQvpXUWznqXbamEdULhzr5BqzgHEwZh-OK-679vBabchGBQz6w44SSQOGEG-B1BVbfbEV4fE2cjUUEUIijFLMamhOpIB7jZaLYUiPpFGn9aT9hSuRrueMbd4GkdTA"
)

os.environ["LOCAL_TEST_JWT"] = JWT_TOKEN

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("e2e_analytics_copilot_test")

# Import analytics-copilot-2 modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from agent import (
    load_analytics_metadata_in_context,
    reconstruct_database_settings_from_analytics_metadata,
    firebase_jwt_var,
    root_agent,
)
from sub_agents.bigquery.tools import get_analytics_metadata, bigquery_nl2sql
from prompts import return_instructions_root
from google.adk.tools import ToolContext

def run_e2e_tests():
    print("\n" + "="*80)
    print("STARTING E2E INTEGRATION TEST: @analytics-copilot-2 <-> customer-identity-service")
    print("="*80)

    # 1. Test direct metadata retrieval via tool with JWT
    print("\n[STEP 1] Fetching analytics metadata directly using JWT...")
    firebase_jwt_var.set(JWT_TOKEN)
    metadata = get_analytics_metadata(token=JWT_TOKEN)
    
    assert metadata is not None, "Metadata response is None"
    assert metadata.get("authorized") is True, f"Expected authorized=True, got {metadata.get('authorized')}"
    print(f"-> Authorized: {metadata.get('authorized')}")
    print(f"-> User Role: {metadata.get('user_role')}")
    print(f"-> Available Datasets: {list(metadata.get('datasets', {}).keys())}")
    
    for ds_name, ds_info in metadata.get("datasets", {}).items():
        tables = list(ds_info.get("tables", {}).keys()) if ds_info.get("tables") else []
        views = list(ds_info.get("views", {}).keys()) if ds_info.get("views") else []
        print(f"   * Dataset: {ds_name}")
        if tables:
            print(f"     Tables ({len(tables)}): {tables}")
        if views:
            print(f"     Views ({len(views)}): {views}")

    # 2. Test schema reconstruction
    print("\n[STEP 2] Reconstructing database settings from analytics metadata...")
    db_settings = reconstruct_database_settings_from_analytics_metadata(metadata)
    schema_objects = db_settings.get("bigquery", {}).get("schema", {})
    print(f"-> Reconstructed {len(schema_objects)} schema objects for BigQuery NL2SQL:")
    for obj_name, obj_data in schema_objects.items():
        print(f"   - {obj_name} ({obj_data.get('object_type')}): {len(obj_data.get('table_schema', []))} columns, SCD2={obj_data.get('is_scd_type_2')}")

    # 3. Test callback loading into agent context
    print("\n[STEP 3] Testing before_agent_callback (load_analytics_metadata_in_context)...")
    callback_context = SimpleNamespace(
        state={},
        session=SimpleNamespace(id="e2e-session-001", user_id="souravmaiti1997@gmail.com")
    )
    load_analytics_metadata_in_context(callback_context)
    
    assert "analytics_metadata" in callback_context.state
    assert "database_settings" in callback_context.state
    assert callback_context.state["user_role"] == "BANK_STAFF"
    print("-> Successfully populated callback_context.state with analytics metadata and database settings.")

    # 4. Test instructions formatting
    print("\n[STEP 4] Testing dynamic root agent instructions formatting...")
    instructions = return_instructions_root(callback_context)
    assert "<ANALYTICS_DATA_CONTEXT>" in instructions
    print(f"-> Generated root agent instructions ({len(instructions)} chars) containing <ANALYTICS_DATA_CONTEXT>.")

    # 5. Test BigQuery NL2SQL with natural language analytical query
    print("\n[STEP 5] Testing NL2SQL generation with analytics metadata...")
    tool_context = SimpleNamespace(
        state=callback_context.state,
    )
    
    test_questions = [
        "What is the total account balance and average customer age grouped by customer segment?",
        "How many active customers do we have across different states?",
    ]
    
    for q in test_questions:
        print(f"\n   Testing Question: \"{q}\"")
        generated_sql = bigquery_nl2sql(question=q, tool_context=tool_context)
        print(f"   Generated SQL:\n{generated_sql}\n")
        assert generated_sql and len(generated_sql) > 10, "Generated SQL is empty"

    print("\n" + "="*80)
    print("ALL E2E INTEGRATION TESTS COMPLETED SUCCESSFULLY!")
    print("="*80 + "\n")

if __name__ == "__main__":
    run_e2e_tests()
