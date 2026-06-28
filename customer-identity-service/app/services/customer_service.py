"""
Customer Service Layer.

Handles high-level business logic relating to customer account mapping,
profile retrieval, and authorized financial account lists.
"""

from app.repositories.customer_repository import CustomerRepository
from app.repositories.identity_repository import IdentityRepository
from app.utils.exceptions import CustomerNotFoundException
from typing import Dict, Any, List

class CustomerService:
    """Service class encapsulating customer identity resolution and authorization boundaries."""

    def __init__(self, customer_repo: CustomerRepository, identity_repo: IdentityRepository):
        """
        Initializes the service with required repository structures.

        Args:
            customer_repo (CustomerRepository): Datastore connector for customer profiles.
            identity_repo (IdentityRepository): Datastore connector for UID mappings.
        """
        self.customer_repo = customer_repo
        self.identity_repo = identity_repo

    def get_customer_by_uid(self, uid: str) -> Dict[str, Any]:
        """
        Resolves a Firebase User UID to a detailed internal customer profile.

        Args:
            uid (str): Authenticated Firebase user identifier.

        Returns:
            Dict[str, Any]: Mapped customer demographic and state metadata.

        Raises:
            CustomerNotFoundException: If no identity mapping or customer record exists.
        """
        identity = self.identity_repo.get_by_uid(uid)
        if not identity:
            raise CustomerNotFoundException(detail="Identity mapping not found for this UID")
        
        customer = self.customer_repo.get_by_id(identity['customer_id'])
        if not customer:
            raise CustomerNotFoundException()
        
        return customer

    def get_authorized_accounts(self, customer_id: int) -> List[Dict[str, str]]:
        """
        Retrieves all active bank products (Savings, Credit Cards, FDs, Loans) owned by the customer.

        Args:
            customer_id (int): Mapped target customer database identifier.

        Returns:
            List[Dict[str, str]]: List of accounts containing account number, product type, and active status.
        """
        all_accounts = []
        
        # Regular checking and savings accounts
        accounts = self.customer_repo.get_accounts(customer_id)
        for acc in accounts:
            all_accounts.append({
                "account_number": acc.get("account_number"),
                "account_type": acc.get("account_type"),
                "account_status": acc.get("account_status")
            })

        # Credit Cards
        credit_cards = self.customer_repo.get_credit_cards(customer_id)
        for cc in credit_cards:
            all_accounts.append({
                "account_number": cc.get("card_account_number"),
                "account_type": cc.get("account_type"),
                "account_status": cc.get("account_status")
            })

        # Fixed Deposits
        fixed_deposits = self.customer_repo.get_fixed_deposits(customer_id)
        for fd in fixed_deposits:
            all_accounts.append({
                "account_number": fd.get("fd_account_number"),
                "account_type": fd.get("account_type"),
                "account_status": fd.get("account_status")
            })

        # Loans
        loans = self.customer_repo.get_loans(customer_id)
        for loan in loans:
            all_accounts.append({
                "account_number": loan.get("loan_account_number"),
                "account_type": loan.get("account_type"),
                "account_status": loan.get("account_status")
            })
        
        return all_accounts

    def get_beneficiary_details(self, customer_id: int) -> List[Dict[str, Any]]:
        """
        Fetches the customer's registered transfer payees (beneficiaries).

        Args:
            customer_id (int): Mapped target customer database identifier.

        Returns:
            List[Dict[str, Any]]: Registered beneficiary records.
        """
        return self.customer_repo.get_beneficiaries(customer_id)
