import warnings
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any

warnings.filterwarnings("ignore", message='Field name "schema"')

class BaseResponseModel(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

class EmailCheckResponse(BaseModel):
    customer_exists: bool
    already_registered: Optional[bool] = None
    is_staff: Optional[bool] = None
    customer_id: Optional[int] = None

class LinkUserResponse(BaseModel):
    customer_id: int
    firebase_uid: str
    registration_completed: bool

class LinkStaffResponse(BaseModel):
    email: str
    firebase_uid: str
    registration_completed: bool

class CustomerMeResponse(BaseModel):
    customer_id: int
    name: str
    email: str
    kyc_status: str
    customer_segment: str

class FieldMetadata(BaseModel):
    column_name: str
    type: str
    description: str
    mode: str

class AuthorizedViewDetail(BaseResponseModel):
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
    customer_profile: Optional[Dict[str, Any]] = None
    authorized_views: Dict[str, AuthorizedViewDetail]
    authorized_account: Optional[List[AccountDetail]] = None

class BeneficiaryDetail(BaseModel):
    beneficiary_id: int
    beneficiary_name: str
    beneficiary_account_number: str
    bank_name: str
    ifsc_code: str
    status: str

class MCPContextResponse(BaseModel):
    customer_id: int
    email: Optional[str] = None
    email_id: Optional[str] = None
    authorized_accounts: List[AccountDetail]
    beneficiary_details: List[BeneficiaryDetail]
    kyc_status: str

class TableMetadataDetail(BaseResponseModel):
    table_name: str
    query_object: str
    logical_name: str
    object_type: str = "TABLE"
    table_description: str
    primary_business_key: Optional[str] = None
    grain: Optional[str] = None
    relationship_information: Optional[str] = None
    is_scd_type_2: bool = False
    scd_columns: List[str] = []
    ai_usage_guidance: Optional[str] = None
    typical_ai_questions: Optional[List[str]] = None
    schema: List[FieldMetadata]

class ViewMetadataDetail(BaseResponseModel):
    view_name: str
    query_object: str
    logical_name: str
    object_type: str = "VIEW"
    table_description: str
    primary_business_key: Optional[str] = None
    grain: Optional[str] = None
    relationship_information: Optional[str] = None
    is_scd_type_2: bool = False
    scd_columns: List[str] = []
    ai_usage_guidance: Optional[str] = None
    typical_ai_questions: Optional[List[str]] = None
    schema: List[FieldMetadata]

class DatasetDetail(BaseModel):
    dataset_description: str
    tables: Optional[Dict[str, TableMetadataDetail]] = None
    views: Optional[Dict[str, ViewMetadataDetail]] = None

class AnalyticsMetadataResponse(BaseModel):
    authorized: bool = True
    user_role: str = "BANK_STAFF"
    datasets: Dict[str, DatasetDetail]

