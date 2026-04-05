from pydantic import BaseModel, EmailStr

# 1. Data for Registration
class UserCreate(BaseModel):
    email: EmailStr
    password: str

# 2. 👉 ADDED: Data for Login
class LoginRequest(BaseModel):
    email: str
    password: str

# 3. Data we send back to the UI (Secure - no passwords!)
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    target_mood: str

    class Config:
        from_attributes = True