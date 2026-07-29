from fastapi import HTTPException, status


def unauthorized(detail: str = 'Unauthorized') -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)
