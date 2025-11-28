from datetime import datetime, timedelta
from typing import Optional, Dict
import hashlib

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt

from ..utils.config_loader import load_settings
from ..services.data_service import DataService  # NEW: needed to read students table

# ---------- Simple hashing (for demo / local use only) ----------

def hash_password(plain_password: str) -> str:
    """Return a hex SHA-256 digest."""
    return hashlib.sha256(plain_password.encode("utf-8")).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password


# ---------- In-memory user store (fixed accounts) ----------

# Demo users:
# admin   / admin123   (admin)
# faculty / faculty123 (faculty)
# advisor / advisor123 (advisor)
#
# NOTE: We do NOT need to hardcode any specific student IDs here.
# Any username that matches a student_id in students.csv and uses
# password "student123" will be treated as a student (see _maybe_make_student_user).
_fake_users_db: Dict[str, Dict] = {
    "admin": {
        "username": "admin",
        "full_name": "Admin User",
        "hashed_password": hash_password("admin123"),
        "role": "admin",
        "student_id": None,
    },
    "faculty": {
        "username": "faculty",
        "full_name": "Faculty Member",
        "hashed_password": hash_password("faculty123"),
        "role": "faculty",
        "student_id": None,
    },
    "advisor": {
        "username": "advisor",
        "full_name": "Advisor User",
        "hashed_password": hash_password("advisor123"),
        "role": "advisor",
        "student_id": None,
    },
}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def get_user(username: str) -> Optional[Dict]:
    return _fake_users_db.get(username)


def _maybe_make_student_user(username: str) -> Optional[Dict]:
    """
    If `username` matches a student_id in the students table,
    synthesize a student user on the fly.

    - Role: "student"
    - student_id: username
    - Password: "student123" (shared demo password)
    """
    # Avoid collisions with fixed admin/faculty/advisor users
    if username in _fake_users_db:
        return None

    # Simple heuristic: treat IDs starting with 'S' as potential student IDs.
    # You can relax this if your IDs use a different format.
    if not username.upper().startswith("S"):
        return None

    # Look up in the data
    data_service = DataService.instance()
    students_df = data_service.get_table("students")

    match = students_df[students_df["student_id"] == username]
    if match.empty:
        return None

    full_name = (
        match["name"].iloc[0]
        if "name" in match.columns and not match["name"].isna().iloc[0]
        else username
    )

    return {
        "username": username,
        "full_name": full_name,
        # Shared demo password; change here if you want a different one.
        "hashed_password": hash_password("student123"),
        "role": "student",
        "student_id": username,
    }


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """
    Authentication logic:

    1. Try built-in fixed accounts (_fake_users_db).
    2. If not found, try to dynamically create a student user based on students.csv.
    """
    # 1) Fixed users
    user = get_user(username)
    if user and verify_password(password, user["hashed_password"]):
        return user

    # 2) Dynamic student user
    dynamic_user = _maybe_make_student_user(username)
    if dynamic_user and verify_password(password, dynamic_user["hashed_password"]):
        return dynamic_user

    return None


# ---------- JWT handling ----------

def _get_auth_settings():
    settings = load_settings()
    return settings["auth"]


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    auth_cfg = _get_auth_settings()
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=auth_cfg["access_token_expire_minutes"])
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, auth_cfg["secret_key"], algorithm=auth_cfg["algorithm"]
    )
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
    auth_cfg = _get_auth_settings()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, auth_cfg["secret_key"], algorithms=[auth_cfg["algorithm"]]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

        # Try fixed users first
        user = get_user(username)
        if user is None:
            # If not a fixed user, try to reconstruct a dynamic student user
            user = _maybe_make_student_user(username)

        if user is None:
            raise credentials_exception

        return user
    except JWTError:
        raise credentials_exception


def require_role(*roles: str):
    """
    Dependency factory: require that current_user['role'] is in roles.
    """

    async def _depend(user: Dict = Depends(get_current_user)) -> Dict:
        if user["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        return user

    return _depend