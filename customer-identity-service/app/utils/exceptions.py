from fastapi import HTTPException, status

class CustomerIdentityException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)

class CustomerNotFoundException(CustomerIdentityException):
    def __init__(self, detail: str = "Customer not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class CustomerAlreadyRegisteredException(CustomerIdentityException):
    def __init__(self, detail: str = "Customer already registered with Firebase"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

class EmailNotVerifiedException(CustomerIdentityException):
    def __init__(self, detail: str = "Firebase email not verified"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

class UnauthorizedException(CustomerIdentityException):
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)
