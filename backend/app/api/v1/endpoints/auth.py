from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.models.user import User, UserRole
from app.models.audit import AuditAction
from app.schemas.user import UserCreate, UserOut, Token, LoginRequest
from app.services.audit_service import log_event
from app.api.deps import get_current_user, require_role

router = APIRouter()


@router.post("/login", response_model=Token)
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT access token."""
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    log_event(
        db=db,
        action=AuditAction.USER_LOGIN,
        actor_id=user.id,
        actor_email=user.email,
        resource_type="user",
        resource_id=str(user.id),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Register a new user. Admin only."""
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_event(
        db=db,
        action=AuditAction.USER_CREATED,
        actor_id=current_user.id,
        actor_email=current_user.email,
        resource_type="user",
        resource_id=str(user.id),
        details={"email": user.email, "role": user.role.value},
    )
    return user


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """Get the currently authenticated user."""
    return current_user
