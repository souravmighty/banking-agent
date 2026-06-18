from pydantic import BaseModel, EmailStr

class EmailCheckRequest(BaseModel):
    email: EmailStr

class LinkUserRequest(BaseModel):
    # The ID token is passed in the Authorization header, but we might need more in the body later
    pass
