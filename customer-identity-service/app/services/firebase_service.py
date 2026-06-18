import firebase_admin
from firebase_admin import auth, credentials
from app.config import settings
from app.utils.exceptions import UnauthorizedException
from typing import Dict, Any

class FirebaseService:
    def __init__(self):
        if not firebase_admin._apps:
            if settings.FIREBASE_SERVICE_ACCOUNT_PATH:
                cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
                firebase_admin.initialize_app(cred)
            else:
                # Use default credentials in Cloud Run environment
                firebase_admin.initialize_app()

    def verify_id_token(self, token: str) -> Dict[str, Any]:
        try:
            decoded_token = auth.verify_id_token(token)
            return decoded_token
        except Exception as e:
            raise UnauthorizedException(detail=f"Invalid Firebase token: {str(e)}")
