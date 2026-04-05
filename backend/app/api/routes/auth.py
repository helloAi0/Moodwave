from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User
from app.core.security import get_password_hash, verify_password, create_access_token

router = APIRouter()

# ✅ REGISTER
@router.post("/register")
async def register(data: dict, db: AsyncSession = Depends(get_db)):
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Missing fields")

    result = await db.execute(select(User).where(User.email == email))
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    user = User(
        email=email,
        # 👇 HERE IS THE FIX 👇
        hashed_password=get_password_hash(password) 
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {"id": user.id, "email": user.email}


# ✅ LOGIN
@router.post("/login")
async def login(data: dict, db: AsyncSession = Depends(get_db)):
    email = data.get("email")
    password = data.get("password")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user.email})

    return {"access_token": token}


# ✅ SPOTIFY CALLBACK (KEEP THIS)
@router.get("/callback")
async def spotify_callback():
    return {"message": "Spotify callback endpoint"}  