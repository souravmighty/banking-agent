#!/usr/bin/env python3
"""Launcher for ADK Web configured with authenticated Bank Staff mock identity and microservice orchestration."""

import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

script_dir = Path(__file__).resolve().parent
analytics_dir = script_dir.parent
repo_root = analytics_dir.parent

# Import the JWT generator
sys.path.insert(0, str(script_dir))
from generate_staff_jwt import generate_mock_staff_jwt  # noqa: E402


def is_port_open(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a TCP port is currently open and accepting connections."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def wait_for_port(port: int, timeout: float = 10.0, host: str = "127.0.0.1") -> bool:
    """Wait until a TCP port starts accepting connections."""
    start = time.time()
    while time.time() - start < timeout:
        if is_port_open(port, host):
            return True
        time.sleep(0.3)
    return False


def main():
    user_id = os.getenv("STAFF_USER_ID", "staff_analyst_01")
    email = os.getenv("STAFF_EMAIL", "sarah.chen@bankpilot.internal")
    name = os.getenv("STAFF_NAME", "Sarah Chen (Senior Portfolio Analyst)")
    port = int(os.getenv("ADK_WEB_PORT", "8502"))

    token = generate_mock_staff_jwt(user_id=user_id, email=email, name=name)

    env = os.environ.copy()
    env["LOCAL_TEST_JWT"] = token
    env["MOCK_AUTH_BYPASS"] = "true"
    env["STAFF_USER_ID"] = user_id
    env["STAFF_EMAIL"] = email
    env["CUSTOMER_IDENTITY_SERVICE_URL"] = "http://localhost:8001"
    env["CUSTOMER_DATA_SERVICE_URL"] = "http://localhost:8081"
    env.pop("VIRTUAL_ENV", None)

    child_processes = []

    def cleanup(signum=None, frame=None):
        """Terminate any background microservices spawned by this launcher."""
        if child_processes:
            print("\n🛑 Stopping background microservices...")
            for proc, proc_name in child_processes:
                if proc.poll() is None:
                    print(f"   Terminating {proc_name} (PID {proc.pid})...")
                    proc.terminate()
            for proc, _ in child_processes:
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
            print("✨ All background services stopped.")
        if signum:
            sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    print("=" * 75)
    print("🚀 Initializing ADK Web for Analytics Copilot (Authenticated Bank Staff)")
    print("=" * 75)

    # 1. Ensure customer-identity-service is running on port 8001
    identity_dir = repo_root / "customer-identity-service"
    if not is_port_open(8001):
        print("⚙️  Starting customer-identity-service on http://localhost:8001...")
        proc_id = subprocess.Popen(
            [
                "uv",
                "run",
                "uvicorn",
                "app.main:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8001",
            ],
            cwd=str(identity_dir),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        child_processes.append((proc_id, "customer-identity-service"))
        if wait_for_port(8001, timeout=8.0):
            print("   ✅ customer-identity-service is live and ready on port 8001.")
        else:
            print("   ⚠️  Timed out waiting for port 8001; continuing with fallback...")
    else:
        print("   ✅ customer-identity-service is already running on port 8001.")

    # 2. Ensure customer-data-service is running on port 8081
    data_dir = repo_root / "customer-data-service"
    if not is_port_open(8081):
        print("⚙️  Starting customer-data-service on http://localhost:8081...")
        proc_data = subprocess.Popen(
            [
                "uv",
                "run",
                "uvicorn",
                "app.main:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8081",
            ],
            cwd=str(data_dir),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        child_processes.append((proc_data, "customer-data-service"))
        if wait_for_port(8081, timeout=8.0):
            print("   ✅ customer-data-service is live and ready on port 8081.")
        else:
            print("   ⚠️  Timed out waiting for port 8081; continuing...")
    else:
        print("   ✅ customer-data-service is already running on port 8081.")

    print("=" * 75)
    print(f"👤 Staff Persona:  {name}")
    print(f"🔑 User ID:        {user_id}")
    print(f"📧 Email:          {email}")
    print("🛡️  Role:           BANK_STAFF")
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
        str(analytics_dir),
    ]

    try:
        subprocess.run(cmd, env=env)
    finally:
        cleanup()


if __name__ == "__main__":
    main()
