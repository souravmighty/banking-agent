import sys
import os

# Adjust path to import app correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.services.bigquery_service import BigQueryService
from app.services.dashboard_service import DashboardService

def main():
    print("Initializing services...")
    bq = BigQueryService()
    service = DashboardService(bq)
    
    test_customer_id = 1248605331019897
    print(f"Fetching aggregated dashboard for customer_id: {test_customer_id}...")
    
    try:
        dashboard = service.get_aggregated_dashboard(test_customer_id)
        print("\n=== DASHBOARD AGGREGATION SUCCESSFUL ===")
        print(f"Customer Name: {dashboard['customer']['name']}")
        print(f"Segment: {dashboard['customer']['segment']}")
        print(f"Summary: {dashboard['summary']}")
        print(f"Number of Accounts: {len(dashboard['accounts'])}")
        print(f"Number of Cards: {len(dashboard['cards'])}")
        print(f"Number of Loans: {len(dashboard['loans'])}")
        print(f"Number of Investments (FDs): {len(dashboard['investments'])}")
        print(f"Number of Recent Transactions: {len(dashboard['recent_transactions'])}")
        print("=========================================\n")
    except Exception as e:
        print(f"Error fetching dashboard: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
