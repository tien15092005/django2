import jwt
import bcrypt
import datetime
from django.conf import settings
from rest_framework.response import Response


# ─── Password ────────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """Trả về chuỗi bcrypt hash dạng string để lưu DB."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def check_password(plain: str, hashed: str) -> bool:
    """So sánh plain text với bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


# ─── JWT ─────────────────────────────────────────────────────────────────────

def generate_token(user_id: str, role: str) -> str:
    """Tạo JWT token có hạn JWT_EXP_HOURS giờ."""
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=settings.JWT_EXP_HOURS),
        'iat': datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    """Giải mã JWT, trả về payload hoặc None nếu lỗi/hết hạn."""
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_current_user(request) -> dict | None:
    """
    Lấy thông tin user từ header Authorization: Bearer <token>.
    Trả về {'user_id': ..., 'role': ...} hoặc None.
    """
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    token = auth.split(' ', 1)[1]
    return decode_token(token)


def require_auth(request):
    """
    Decorator-helper dùng trong view.
    Trả về (payload, None) nếu hợp lệ.
    Trả về (None, Response 401) nếu không hợp lệ.
    """
    payload = get_current_user(request)
    if not payload:
        return None, Response({'error': 'Unauthorized – token không hợp lệ hoặc hết hạn'}, status=401)
    return payload, None


def require_admin(request):
    """
    Chỉ cho phép role = 'admin'.
    Trả về (payload, None) nếu hợp lệ.
    Trả về (None, Response 401/403) nếu không.
    """
    payload, err = require_auth(request)
    if err:
        return None, err
    if payload.get('role') != 'admin':
        return None, Response({'error': 'Forbidden – chỉ admin mới được thực hiện'}, status=403)
    return payload, None