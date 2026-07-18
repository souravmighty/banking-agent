import os
import sys
import firebase_admin
from firebase_admin import credentials, auth

# Ensure we can import app
sys.path.append(os.getcwd())
from app.config import settings

def main():
    # Initialize with Application Default Credentials (active gcloud user)
    try:
        firebase_admin.initialize_app()
    except Exception as init_err:
        print(f"Default init failed, falling back to service account: {init_err}")
        if not settings.FIREBASE_SERVICE_ACCOUNT_PATH:
            print("Error: FIREBASE_SERVICE_ACCOUNT_PATH is not set.")
            return
        cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
        firebase_admin.initialize_app(cred)
    
    email = "souravmaiti1997@gmail.com"
    print(f"Checking user: {email}")
    try:
        user = auth.get_user_by_email(email)
        print(f"-> User exists in Firebase Auth! UID: {user.uid}, email_verified: {user.email_verified}")
        print("-> Deleting user to allow a fresh password creation setup...")
        auth.delete_user(user.uid)
        print("-> User deleted successfully from Firebase Auth!")
    except auth.UserNotFoundError:
        print("-> User does not exist in Firebase Auth (clean state).")
    except Exception as e:
        print(f"-> Error: {e}")

if __name__ == "__main__":
    main()
