from fastapi import Depends, Request
from . import require_admin


def admin_guard(request: Request) -> None:
    require_admin(request)
