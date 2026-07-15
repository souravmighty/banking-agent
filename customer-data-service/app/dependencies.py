import os
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.cloud import bigquery
from app.config import settings
from app.services.bigquery_service import BigQueryService
from app.services.firebase_service import FirebaseService
from typing import Dict, Any, Optional

# Singletons
_bq_service = BigQueryService()
_firebase_service = FirebaseService()
security = HTTPBearer(auto_error=False)

def get_bq_service() -> BigQueryService:
    return _bq_service

def get_firebase_service() -> FirebaseService:
    return _firebase_service

async def get_current_user(
    auth_creds: Optional[HTTPAuthorizationCredentials] = Depends(security),
    firebase_service: FirebaseService = Depends(get_firebase_service),
    bq_service: BigQueryService = Depends(get_bq_service)
) -> Dict[str, Any]:
    token = None
    if auth_creds:
        token = auth_creds.credentials

    # Check for local developer mode bypass
    mock_auth_bypass = settings.MOCK_AUTH_BYPASS

    if not token or token == "mock-token" or token == "":
        if mock_auth_bypass:
            # Fallback mock identity email from environment or default
            email = os.getenv("CUSTOMER_EMAIL_ID", "souravmaiti1997@gmail.com")
            return {
                "uid": f"mock-uid-fallback",
                "email": email,
                "is_mock": True
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token is missing or empty"
            )

    # Handle mock tokens (e.g., mock-token:email or mock-token:uid)
    if token.startswith("mock-token:"):
        val = token.split(":", 1)[1]
        if "@" in val:
            return {
                "uid": f"mock-uid-{val}",
                "email": val,
                "is_mock": True
            }
        else:
            return {
                "uid": val,
                "email": f"mock-{val}@bankpilot.dev",
                "is_mock": True
            }

    try:
        decoded_token = firebase_service.verify_id_token(token)
        return decoded_token
    except Exception as e:
        # Fallback/Decoding for debugging or if bypass is enabled
        if mock_auth_bypass:
            try:
                parts = token.split(".")
                if len(parts) >= 2:
                    import base64
                    import json
                    payload_b64 = parts[1]
                    padding = len(payload_b64) % 4
                    if padding:
                        payload_b64 += "=" * (4 - padding)
                    payload_bytes = base64.urlsafe_b64decode(payload_b64)
                    payload = json.loads(payload_bytes.decode('utf-8'))
                    return {
                        "uid": payload.get("user_id") or payload.get("sub") or "mock-uid",
                        "email": payload.get("email") or "mock@bankpilot.dev",
                        "is_mock": True
                    }
            except Exception:
                pass
            
            email = os.getenv("CUSTOMER_EMAIL_ID", "souravmaiti1997@gmail.com")
            return {
                "uid": f"mock-uid-fallback",
                "email": email,
                "is_mock": True
            }
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired credentials: {str(e)}"
        )

async def get_current_customer_id(
    current_user: Dict[str, Any] = Depends(get_current_user),
    bq_service: BigQueryService = Depends(get_bq_service)
) -> int:
    uid = current_user.get("uid")
    email = current_user.get("email")

    # If mock token explicitly embedded the customer_id
    if uid and uid.startswith("mock-uid-") and not uid.endswith("fallback"):
        try:
            return int(uid.split("-")[-1])
        except ValueError:
            pass

    # Query customer mapping
    mapping_table = f"`{settings.GOOGLE_CLOUD_PROJECT}.{settings.BIGQUERY_DATASET}.customer_identity_mapping`"
    
    query = f"""
        SELECT customer_id FROM {mapping_table}
        WHERE firebase_uid = @uid OR LOWER(email_id) = LOWER(@email)
        LIMIT 1
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("uid", "STRING", uid),
            bigquery.ScalarQueryParameter("email", "STRING", email)
        ]
    )
    
    try:
        results = bq_service.execute_query(query, job_config=job_config)
        if results:
            return results[0]["customer_id"]
    except Exception as e:
        # If we are in bypass mode, default to a fallback customer_id (e.g. 1) to prevent blockage
        if settings.MOCK_AUTH_BYPASS:
            # Let's see if there is any active mapping in the pool we can grab
            try:
                fallback_query = f"SELECT customer_id FROM {mapping_table} LIMIT 1"
                fallback_res = bq_service.execute_query(fallback_query)
                if fallback_res:
                    return fallback_res[0]["customer_id"]
            except Exception:
                pass
            return 1
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database query failed while fetching customer mapping: {str(e)}"
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No pre-authorized bank customer mapping found for this authenticated user."
    )
