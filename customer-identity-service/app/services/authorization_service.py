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
        staff = self.identity_repo.get_staff_by_email(email)
        is_staff = self.identity_repo.is_staff_email(email)
        
        customer_exists = mapping is not None
        already_registered = False
        if mapping and mapping.get("firebase_uid"):
            already_registered = True
        elif staff and staff.get("firebase_uid"):
            already_registered = True

        return {
            "customer_exists": customer_exists,
            "is_staff": is_staff,
            "already_registered": already_registered,
            "customer_id": mapping.get("customer_id") if mapping else None
        }

    def link_staff_user(self, decoded_token: Dict[str, Any]) -> Dict[str, Any]:
        uid = decoded_token["uid"]
        email = decoded_token["email"]

        staff = self.identity_repo.get_staff_by_email(email)
        if not staff:
            raise CustomerNotFoundException(detail="Email not found in our pre-authorized bank staff list")

        if staff.get("firebase_uid") and staff["firebase_uid"] != uid:
             raise CustomerAlreadyRegisteredException()

        # Update dynamic bank staff table
        self.identity_repo.link_staff_uid(email, uid)

        return {
            "email": email,
            "firebase_uid": uid,
            "registration_completed": True
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

        # Check and handle demo customer state transition to ACTIVE on Google login
        try:
            from app.repositories.demo_repository import DemoRepository
            demo_repo = DemoRepository(self.identity_repo.bq)
            demo_cust = demo_repo.get_by_demo_email(email)
            if demo_cust and demo_cust["status"] == "APPROVED":
                demo_repo.update_status_to_active(demo_cust["customer_id"], uid)
                demo_repo.log_audit(
                    action="Google Login",
                    customer_id=demo_cust["customer_id"],
                    demo_email=email,
                    firebase_uid=uid,
                    performed_by=email,
                    remarks="Demo customer completed Google Sign-In and linked account successfully."
                )
        except Exception as e:
            # Prevent failures in demo lookup from breaking core login flows
            import logging
            logging.getLogger(__name__).error(f"Error handling demo customer login state: {e}")

        # Create views
        self.view_service.create_authorized_views(mapping["customer_id"])

        return {
            "customer_id": mapping["customer_id"],
            "firebase_uid": uid,
            "registration_completed": True
        }

