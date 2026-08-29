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
            # Fallback to check if this is a registered bank staff
            staff = self.identity_repo.get_staff_by_uid(uid)
            if staff:
                return {
                    "customer_id": 0,
                    "name": staff.get("name") or "Bank Staff",
                    "email": staff.get("email"),
                    "kyc_status": "VERIFIED",
                    "customer_segment": "STAFF"
                }
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
        seen_accounts = set()
        
        # Regular checking and savings accounts
        accounts = self.customer_repo.get_accounts(customer_id)
        for acc in accounts:
            acc_num = acc.get("account_number")
            if acc_num and acc_num not in seen_accounts:
                seen_accounts.add(acc_num)
                all_accounts.append({
                    "account_number": acc_num,
                    "account_type": acc.get("account_type"),
                    "account_status": acc.get("account_status")
                })

        # Credit Cards
        credit_cards = self.customer_repo.get_credit_cards(customer_id)
        for cc in credit_cards:
            card_acc = cc.get("card_account_number")
            if card_acc and card_acc not in seen_accounts:
                seen_accounts.add(card_acc)
                all_accounts.append({
                    "account_number": card_acc,
                    "account_type": cc.get("account_type"),
                    "account_status": cc.get("account_status")
                })

        # Fixed Deposits
        fixed_deposits = self.customer_repo.get_fixed_deposits(customer_id)
        for fd in fixed_deposits:
            fd_acc = fd.get("fd_account_number")
            if fd_acc and fd_acc not in seen_accounts:
                seen_accounts.add(fd_acc)
                all_accounts.append({
                    "account_number": fd_acc,
                    "account_type": fd.get("account_type"),
                    "account_status": fd.get("account_status")
                })

        # Loans
        loans = self.customer_repo.get_loans(customer_id)
        for loan in loans:
            loan_acc = loan.get("loan_account_number")
            if loan_acc and loan_acc not in seen_accounts:
                seen_accounts.add(loan_acc)
                all_accounts.append({
                    "account_number": loan_acc,
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
