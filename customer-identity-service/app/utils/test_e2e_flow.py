import os
import sys
from datetime import datetime, timezone

# Ensure we can import app
sys.path.append(os.getcwd())

from app.services.bigquery_service import BigQueryService
from app.repositories.demo_repository import DemoRepository
from app.repositories.identity_repository import IdentityRepository
from app.services.demo_service import DemoService
from app.services.view_service import ViewService
from app.services.authorization_service import AuthorizationService

def run_e2e_test():
    print("="*60)
    print("STARTING E2E INTEGRATION TEST FOR DEMO ALLOCATION WORKFLOW")
    print("="*60)
    
    bq = BigQueryService()
    demo_repo = DemoRepository(bq)
    identity_repo = IdentityRepository(bq)
    view_service = ViewService(bq)
    demo_service = DemoService(demo_repo, view_service)
    auth_service = AuthorizationService(identity_repo, view_service)

    # 1. Check all demo customers
    print("\n1. Listing all demo customers in the pool...")
    customers = demo_service.get_all_demo_customers()
    print(f"Total customers in pool: {len(customers)}")
    available = [c for c in customers if c["status"] == "AVAILABLE"]
    print(f"Available customers: {len(available)}")
    
    # Proactively clean up any existing allocation for the test email to make the test repeatable
    try:
        existing_demo = demo_service.get_demo_status("john.recruiter@gmail.com")
        if existing_demo:
            print(f"Test email john.recruiter@gmail.com already allocated to customer {existing_demo['customer_id']}. Releasing...")
            demo_service.release_demo_customer(str(existing_demo["customer_id"]), performed_by="System", remarks="Test repeatability cleanup")
            # Refresh customers list
            customers = demo_service.get_all_demo_customers()
            available = [c for c in customers if c["status"] == "AVAILABLE"]
    except Exception:
        pass

    if len(available) == 0:
        print("No available customer in pool. Releasing first one to start clean...")
        first_cust_id = customers[0]["customer_id"]
        demo_service.release_demo_customer(str(first_cust_id), performed_by="System", remarks="Test cleanup")
        customers = demo_service.get_all_demo_customers()
        available = [c for c in customers if c["status"] == "AVAILABLE"]
        print(f"Available customers after cleanup: {len(available)}")

    # 2. Allocate the customer
    test_email = "john.recruiter@gmail.com"
    test_name = "John Recruiter"
    print(f"\n2. Allocating an available customer to {test_name} ({test_email})...")

    alloc_res = demo_service.allocate_demo_customer(
        name=test_name,
        email=test_email,
        approved_by="Sourav"
    )
    print("Allocation result:", alloc_res)
    assert alloc_res["status"] == "APPROVED"
    
    cust_id = str(alloc_res["customer_id"])
    target_cust = [c for c in customers if str(c["customer_id"]) == cust_id][0]
    print(f"Successfully matched allocated customer ID: {cust_id} (Original Name: {target_cust['original_name']}, Email: {target_cust['original_email']})")


    # Verify database states
    print("\n3. Verifying updated database states...")
    # Get from demo_customers
    demo_status = demo_service.get_demo_status(test_email)
    print("demo_customers state:", {k: demo_status[k] for k in ["status", "demo_name", "demo_email", "allocated_by"]})
    assert demo_status["status"] == "APPROVED"
    assert demo_status["demo_name"] == test_name
    assert demo_status["demo_email"] == test_email

    # Get from base customers table
    cust_record = bq.execute_query(
        f"SELECT name, email FROM `{demo_repo.customers_table}` WHERE customer_id = {cust_id} AND is_current = TRUE"
    )[0]
    print("Base customers state:", cust_record)
    assert cust_record["name"] == test_name
    assert cust_record["email"] == test_email

    # Get from identity mapping table
    mapping_record = bq.execute_query(
        f"SELECT email_id, firebase_uid, registration_status, linked_at FROM `{demo_repo.mapping_table}` WHERE customer_id = {cust_id}"
    )[0]
    print("customer_identity_mapping state:", mapping_record)
    assert mapping_record["email_id"] == test_email
    assert mapping_record["registration_status"] == "NOT REGISTERED"
    assert mapping_record["firebase_uid"] is None

    # 4. Simulate user Google Sign-In and Linking
    print(f"\n4. Simulating Google login and link-user for {test_email}...")
    decoded_token = {
        "uid": "recruiter-firebase-uid-999",
        "email": test_email,
        "email_verified": True
    }
    link_res = auth_service.link_firebase_user(decoded_token)
    print("Linking result:", link_res)
    assert link_res["customer_id"] == int(cust_id)
    assert link_res["registration_completed"] is True

    # Verify demo customer status became ACTIVE
    demo_status = demo_service.get_demo_status(test_email)
    print("demo_customers after login state:", {k: demo_status[k] for k in ["status", "firebase_uid"]})
    assert demo_status["status"] == "ACTIVE"
    assert demo_status["firebase_uid"] == "recruiter-firebase-uid-999"

    # Verify identity mapping became REGISTERED
    mapping_record = bq.execute_query(
        f"SELECT email_id, firebase_uid, registration_status, linked_at FROM `{demo_repo.mapping_table}` WHERE customer_id = {cust_id}"
    )[0]
    print("customer_identity_mapping after login state:", mapping_record)
    assert mapping_record["registration_status"] == "REGISTERED"
    assert mapping_record["firebase_uid"] == "recruiter-firebase-uid-999"

    # Verify BigQuery views exist
    print("\n5. Verifying BigQuery views creation...")
    views = bq.client.list_tables(view_service.target_dataset)
    prefix = f"customer_{cust_id}_"
    customer_views = [t.table_id for t in views if t.table_id.startswith(prefix)]
    print(f"Created views for customer {cust_id}:", customer_views)
    assert len(customer_views) > 0

    # 5. Release customer
    print(f"\n6. Releasing customer {cust_id} back to pool...")
    release_res = demo_service.release_demo_customer(cust_id, performed_by="System", remarks="End of integration test")
    print("Release result:", release_res)
    assert release_res["status"] == "AVAILABLE"
    assert release_res["deleted_views_count"] > 0

    # Verify fully restored states
    print("\n7. Verifying fully restored states...")
    demo_status = demo_service.get_all_demo_customers()
    target_demo_record = [r for r in demo_status if str(r["customer_id"]) == cust_id][0]
    print("demo_customers restored state:", {k: target_demo_record[k] for k in ["status", "demo_name", "demo_email", "firebase_uid"]})
    assert target_demo_record["status"] == "AVAILABLE"
    assert target_demo_record["demo_name"] is None
    assert target_demo_record["demo_email"] is None

    cust_record = bq.execute_query(
        f"SELECT name, email FROM `{demo_repo.customers_table}` WHERE customer_id = {cust_id} AND is_current = TRUE"
    )[0]
    print("Base customers restored state:", cust_record)
    assert cust_record["name"] == target_cust["original_name"]
    assert cust_record["email"] == target_cust["original_email"]

    mapping_record = bq.execute_query(
        f"SELECT email_id, firebase_uid, registration_status FROM `{demo_repo.mapping_table}` WHERE customer_id = {cust_id}"
    )[0]
    print("customer_identity_mapping restored state:", mapping_record)
    assert mapping_record["email_id"] == target_cust["original_email"]
    assert mapping_record["registration_status"] == "NOT REGISTERED"
    assert mapping_record["firebase_uid"] is None

    # Verify BigQuery views deleted
    views = bq.client.list_tables(view_service.target_dataset)
    customer_views_after = [t.table_id for t in views if t.table_id.startswith(prefix)]
    print(f"Views after release (should be empty):", customer_views_after)
    assert len(customer_views_after) == 0

    print("\n" + "="*60)
    print("ALL E2E INTEGRATION TESTS PASSED SUCCESSFULLY! WORKFLOW IS 100% CORRECT!")
    print("="*60 + "\n")

if __name__ == "__main__":
    run_e2e_test()
