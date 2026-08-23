#!/usr/bin/env python3
"""Launcher for ADK Web configured with authenticated Bank Staff mock identity."""

import os
import subprocess
import sys
from pathlib import Path

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent

# Import the JWT generator
sys.path.insert(0, str(script_dir))
from generate_staff_jwt import generate_mock_staff_jwt


def main():
    user_id = os.getenv("STAFF_USER_ID", "staff_analyst_01")
    email = os.getenv("STAFF_EMAIL", "sarah.chen@bankpilot.internal")
    name = os.getenv("STAFF_NAME", "Sarah Chen (Senior Portfolio Analyst)")
    port = os.getenv("ADK_WEB_PORT", "8502")

    token = generate_mock_staff_jwt(user_id=user_id, email=email, name=name)

    env = os.environ.copy()
    env["LOCAL_TEST_JWT"] = token
    env["MOCK_AUTH_BYPASS"] = "true"
    env["STAFF_USER_ID"] = user_id
    env["STAFF_EMAIL"] = email

    print("=" * 75)
    print("🚀 Starting ADK Web for Analytics Copilot (Authenticated Bank Staff)")
    print("=" * 75)
    print(f"👤 Staff Persona:  {name}")
    print(f"🔑 User ID:        {user_id}")
    print(f"📧 Email:          {email}")
    print(f"🛡️  Role:           BANK_STAFF")
    print(f"🌐 ADK Web URL:    http://localhost:{port}")
    print("=" * 75)
    print(f"💡 In ADK Web sidebar, set 'User ID' to: {user_id}")
    print("=" * 75 + "\n")

    cmd = [
        "uv",
        "run",
        "adk",
        "web",
        "--port",
        str(port),
        str(project_root),
    ]

    subprocess.run(cmd, env=env)


if __name__ == "__main__":
    main()
