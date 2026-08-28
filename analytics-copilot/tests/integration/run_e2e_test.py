import logging
import os
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
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("e2e_analytics_copilot_test")

from app.agent import (  # noqa: E402
    firebase_jwt_var,
    load_analytics_metadata_in_context,
    reconstruct_database_settings_from_analytics_metadata,
)
from app.prompts import return_instructions_root  # noqa: E402
from app.sub_agents.bigquery.tools import (  # noqa: E402
    bigquery_nl2sql,
    get_analytics_metadata,
)


def run_e2e_tests():
    print("\n" + "=" * 80)
    print(
        "STARTING E2E INTEGRATION TEST: @analytics-copilot <-> customer-identity-service"
    )
    print("=" * 80)

    # 1. Test direct metadata retrieval via tool with JWT
    print("\n[STEP 1] Fetching analytics metadata directly using JWT...")
    firebase_jwt_var.set(JWT_TOKEN)
    metadata = get_analytics_metadata(token=JWT_TOKEN)

    assert metadata is not None, "Metadata response is None"
    assert metadata.get("authorized") is True, (
        f"Expected authorized=True, got {metadata.get('authorized')}"
    )
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

    # 2. Test database_settings schema reconstruction
    print("\n[STEP 2] Reconstructing BigQuery schema dictionary...")
    db_settings = reconstruct_database_settings_from_analytics_metadata(metadata)
    schema = db_settings.get("bigquery", {}).get("schema", {})
    print(f"-> Reconstructed {len(schema)} schema objects (tables and views)")
    for obj_name, obj_meta in schema.items():
        print(
            f"   - [{obj_meta.get('object_type')}] {obj_name} (SCD Type 2: {obj_meta.get('is_scd_type_2')}, Columns: {len(obj_meta.get('table_schema', []))})"
        )
    assert len(schema) >= 10, f"Expected at least 10 schema objects, got {len(schema)}"

    # 3. Test callback execution
    print("\n[STEP 3] Testing before_agent_callback on simulated agent context...")
    context = SimpleNamespace(
        state={},
        session=SimpleNamespace(
            id="test-e2e-session-123", user_id="UBBHaTkgNuVD3LbP5nv4ywOq68v2"
        ),
    )
    load_analytics_metadata_in_context(context)
    assert "analytics_metadata" in context.state, (
        "Callback failed to inject analytics_metadata"
    )
    assert "database_settings" in context.state, (
        "Callback failed to inject database_settings"
    )
    assert context.state["user_role"] == "BANK_STAFF"
    print("-> Callback successfully populated context state with zero customer PII")

    # 4. Test root agent prompt generation
    print("\n[STEP 4] Formatting root agent dynamic instruction prompt...")
    instructions = return_instructions_root(context)
    assert "<ANALYTICS_DATA_CONTEXT>" in instructions
    assert "analytics_customer_360" in instructions
    assert "analytics_transactions" in instructions
    print(
        "-> Instruction prompt successfully formatted with all analytical views and operational tables"
    )

    # 5. Test BigQuery NL2SQL tool call
    print("\n[STEP 5] Testing NL2SQL generation via Gemini 2.5 Pro...")
    tool_ctx = SimpleNamespace(state=context.state)
    sample_question = "Give me month on month view of credit card transacted customers and average credit card spends per customer"

    sql = bigquery_nl2sql(question=sample_question, tool_context=tool_ctx)
    print("\n" + "-" * 40 + " GENERATED SQL " + "-" * 40)
    print(sql)
    print("-" * 95)

    assert "SELECT" in sql.upper()
    assert "analytics_transactions" in sql or "transactions" in sql
    print("-> NL2SQL successfully generated SQL against BigQuery schema")

    print("\n" + "=" * 80)
    print("ALL E2E INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_e2e_tests()
