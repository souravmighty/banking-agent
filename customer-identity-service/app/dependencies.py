from fastapi import Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.bigquery_service import BigQueryService
from app.services.firebase_service import FirebaseService
from app.services.view_service import ViewService
from app.services.customer_service import CustomerService
from app.services.authorization_service import AuthorizationService
from app.repositories.customer_repository import CustomerRepository
from app.repositories.identity_repository import IdentityRepository
from app.utils.exceptions import UnauthorizedException
from typing import Dict, Any

# Singleton services (managed by DI)
_bq_service = BigQueryService()
_firebase_service = FirebaseService()
security = HTTPBearer()

def get_bq_service() -> BigQueryService:
    return _bq_service

def get_firebase_service() -> FirebaseService:
    return _firebase_service

def get_identity_repository(bq: BigQueryService = Depends(get_bq_service)) -> IdentityRepository:
    return IdentityRepository(bq)

def get_customer_repository(bq: BigQueryService = Depends(get_bq_service)) -> CustomerRepository:
    return CustomerRepository(bq)

def get_view_service(bq: BigQueryService = Depends(get_bq_service)) -> ViewService:
    return ViewService(bq)

def get_customer_service(
    customer_repo: CustomerRepository = Depends(get_customer_repository),
    identity_repo: IdentityRepository = Depends(get_identity_repository)
) -> CustomerService:
    return CustomerService(customer_repo, identity_repo)

def get_authorization_service(
    identity_repo: IdentityRepository = Depends(get_identity_repository),
    view_service: ViewService = Depends(get_view_service)
) -> AuthorizationService:
    return AuthorizationService(identity_repo, view_service)

async def get_current_user(
    auth_creds: HTTPAuthorizationCredentials = Depends(security),
    firebase_service: FirebaseService = Depends(get_firebase_service)
) -> Dict[str, Any]:
    token = auth_creds.credentials
    return firebase_service.verify_id_token(token)
