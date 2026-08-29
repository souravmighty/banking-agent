import os
import json
import logging
from app.sub_agents.bigquery.tools import get_customer_profile, get_database_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_integration")

def main():
    email = "jane39@example.com"
    logger.info("Testing get_customer_profile for: %s", email)
    profile = get_customer_profile(email)
    logger.info("Successfully fetched customer profile:")
    print(json.dumps(profile, indent=2))
    
    logger.info("Testing get_database_settings for: %s", email)
    settings = get_database_settings(email)
    logger.info("Successfully fetched database settings:")
    print(json.dumps(settings, indent=2))

if __name__ == "__main__":
    main()
