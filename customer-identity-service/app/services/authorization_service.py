from app.repositories.identity_repository import IdentityRepository
from app.services.view_service import ViewService
from app.utils.exceptions import (
    CustomerNotFoundException, 
    CustomerAlreadyRegisteredException,
    EmailNotVerifiedException
)
from typing import Dict, Any

class AuthorizationService:
    def __init__(self, identity_repo: IdentityRepository, view_service: ViewService):
        self.identity_repo = identity_repo
        self.view_service = view_service

    def check_email_availability(self, email: str) -> Dict[str, Any]:
        mapping = self.identity_repo.get_by_email(email)
        if not mapping:
            return {"customer_exists": False}
        
        return {
            "customer_exists": True,
            "already_registered": mapping.get("firebase_uid") is not None
        }

    def link_firebase_user(self, decoded_token: Dict[str, Any]) -> Dict[str, Any]:
        if not decoded_token.get("email_verified"):
            raise EmailNotVerifiedException()

        uid = decoded_token["uid"]
        email = decoded_token["email"]

        mapping = self.identity_repo.get_by_email(email)
        if not mapping:
            raise CustomerNotFoundException(detail="Email not found in our pre-authorized customer list")

        if mapping.get("firebase_uid") and mapping["firebase_uid"] != uid:
             raise CustomerAlreadyRegisteredException()

        # Update mapping with UID, status and timestamp
        from datetime import datetime
        linked_at = datetime.now().isoformat()
        self.identity_repo.update_firebase_uid(mapping["customer_id"], uid, "REGISTERED", linked_at)

        # Create views
        self.view_service.create_authorized_views(mapping["customer_id"])

        return {
            "customer_id": mapping["customer_id"],
            "firebase_uid": uid,
            "registration_completed": True
        }
