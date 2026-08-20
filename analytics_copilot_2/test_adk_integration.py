import os
import json
import logging
from sub_agents.bigquery.tools import get_analytics_metadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_integration")

def main():
    token = os.getenv("LOCAL_TEST_JWT", "mock-token:staff@bank.com")
    logger.info("Testing get_analytics_metadata...")
    metadata = get_analytics_metadata(token=token)
    logger.info("Successfully fetched analytics metadata:")
    print(json.dumps(metadata, indent=2))

if __name__ == "__main__":
    main()
