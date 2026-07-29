import base64
import hashlib
import hmac
import os
import time
from fastapi import HTTPException, Request, Response
from fastapi import status as http_status
from ..utils.logger import logger

PIN_CODE = os.getenv('PIN_CODE', '1234')
SECRET_KEY = os.getenv('SECRET_KEY', 'karaoke-secret-key').encode('utf-8')
TOKEN_EXPIRE_SECONDS = int(os.getenv('PIN_TOKEN_EXPIRE_SECONDS', '3600'))
TOKEN_COOKIE_NAME = 'karaoke_admin_token'
TOKEN_HEADER_PREFIX = 'Bearer '


def _pad_base64(encoded: str) -> str:
    return encoded + '=' * (-len(encoded) % 4)


def _make_signature(payload: bytes) -> bytes:
    return hmac.new(SECRET_KEY, payload, hashlib.sha256).digest()


def _build_token(timestamp: int) -> str:
    payload = f'karaoke-admin:{timestamp}'.encode('utf-8')
    signature = _make_signature(payload)
    return base64.urlsafe_b64encode(payload + b'.' + signature).decode('utf-8')


def _parse_token(token: str) -> tuple[bytes, bytes] | None:
    try:
        decoded = base64.urlsafe_b64decode(_pad_base64(token))
        payload, signature = decoded.rsplit(b'.', 1)
        return payload, signature
    except Exception as exc:
        logger.debug('Failed to parse auth token: %s', exc)
        return None


def create_token() -> str:
    return _build_token(int(time.time()))


def verify_token(token: str) -> bool:
    parsed = _parse_token(token)
    if parsed is None:
        return False
    payload, signature = parsed
    expected = _make_signature(payload)
    if not hmac.compare_digest(signature, expected):
        return False
    try:
        payload_text = payload.decode('utf-8')
        prefix, timestamp_str = payload_text.split(':', 1)
        if prefix != 'karaoke-admin':
            return False
        timestamp = int(timestamp_str)
    except Exception:
        return False
    if time.time() - timestamp > TOKEN_EXPIRE_SECONDS:
        return False
    return True


def authenticate_pin(pin: str) -> bool:
    return pin == PIN_CODE


def get_token_from_request(request: Request) -> str | None:
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith(TOKEN_HEADER_PREFIX):
        return auth_header[len(TOKEN_HEADER_PREFIX) :].strip()
    return request.cookies.get(TOKEN_COOKIE_NAME)


def is_authenticated(request: Request) -> bool:
    token = get_token_from_request(request)
    return bool(token and verify_token(token))


def require_admin(request: Request) -> None:
    if not is_authenticated(request):
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail='Unauthorized')


def set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        TOKEN_COOKIE_NAME,
        token,
        httponly=True,
        max_age=TOKEN_EXPIRE_SECONDS,
        secure=False,
        samesite='lax',
    )


def clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(TOKEN_COOKIE_NAME)
