#!/usr/bin/env python3
"""Utility script to generate mock JWT tokens for Bank Staff authentication in local ADK Web and CLI testing."""

import argparse
import base64
import json
import time


def generate_mock_staff_jwt(
    user_id: str = "staff_analyst_01",
    email: str = "sarah.chen@bankpilot.internal",
    name: str = "Sarah Chen (Senior Portfolio Analyst)",
    role: str = "BANK_STAFF",
    branch_id: str = "BR-HQ-001",
) -> str:
    """Generate a mock JWT token with standard claims for Bank Staff."""
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "iss": "https://securetoken.google.com/banking-agent-rag-mcp",
        "aud": "banking-agent-rag-mcp",
        "auth_time": now,
        "user_id": user_id,
        "sub": user_id,
        "uid": user_id,
        "email": email,
        "email_verified": True,
        "name": name,
        "role": role,
        "user_role": role,
        "roles": [role, "ANALYTICS_USER", "PORTFOLIO_ANALYST"],
        "branch_id": branch_id,
        "permissions": ["ANALYTICS_READ", "PORTFOLIO_READ", "METADATA_READ"],
        "iat": now,
        "exp": now + 86400 * 365,  # 1 year validity
    }

    def b64_encode(data: dict) -> str:
        json_bytes = json.dumps(data, separators=(",", ":")).encode("utf-8")
        return base64.urlsafe_b64encode(json_bytes).decode("utf-8").rstrip("=")

    header_b64 = b64_encode(header)
    payload_b64 = b64_encode(payload)
    mock_signature = "mock_adk_staff_signature_for_local_development"

    return f"{header_b64}.{payload_b64}.{mock_signature}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Mock Bank Staff JWT")
    parser.add_argument("--user-id", default="staff_analyst_01", help="Bank staff User ID")
    parser.add_argument("--email", default="sarah.chen@bankpilot.internal", help="Bank staff Email")
    parser.add_argument("--name", default="Sarah Chen (Senior Portfolio Analyst)", help="Staff Name")
    parser.add_argument("--role", default="BANK_STAFF", help="Staff Role")
    parser.add_argument("--branch", default="BR-HQ-001", help="Branch ID")
    parser.add_argument("--export", action="store_true", help="Print export statements for shell eval")

    args = parser.parse_args()
    token = generate_mock_staff_jwt(
        user_id=args.user_id,
        email=args.email,
        name=args.name,
        role=args.role,
        branch_id=args.branch,
    )

    if args.export:
        print(f'export LOCAL_TEST_JWT="{token}"')
        print(f'export MOCK_AUTH_BYPASS="true"')
        print(f'export DEFAULT_STAFF_USER_ID="{args.user_id}"')
    else:
        print(token)
