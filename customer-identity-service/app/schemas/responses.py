from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class EmailCheckResponse(BaseModel):
    customer_exists: bool
    already_registered: Optional[bool] = None

class LinkUserResponse(BaseModel):
    customer_id: int
    firebase_uid: str
    registration_completed: bool

class CustomerMeResponse(BaseModel):
    customer_id: int
    name: str
    email: str
    kyc_status: str

class FieldMetadata(BaseModel):
    column_name: str
    type: str
    description: str
    mode: str

class AuthorizedViewDetail(BaseModel):
    view_name: str
    table_description: str
    ai_usage_guidance: Optional[str] = None
    is_scd_type_2: bool
    scd_columns: List[str]
    schema: List[FieldMetadata]

class AccountDetail(BaseModel):
    account_number: str
    account_type: str
    account_status: str

class ADKContextResponse(BaseModel):
    customer_id: int
    customer: Optional[Dict[str, Any]] = None
    authorized_views: List[AuthorizedViewDetail]
    authorized_accounts: Optional[List[AccountDetail]] = None

class BeneficiaryDetail(BaseModel):
    beneficiary_id: int
    beneficiary_name: str
    beneficiary_account_number: str
    bank_name: str
    ifsc_code: str
    status: str

class MCPContextResponse(BaseModel):
    customer_id: int
    authorized_accounts: List[AccountDetail]
    beneficiary_details: List[BeneficiaryDetail]
    kyc_status: str
