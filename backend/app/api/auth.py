from fastapi import APIRouter, Request, Response, Depends, HTTPException, status
from ..schemas.auth import AuthRequest, AuthResponse
from ..auth import authenticate_pin, create_token, set_auth_cookie, clear_auth_cookie, is_authenticated

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/login', response_model=AuthResponse)
def login(auth: AuthRequest, response: Response):
    if not authenticate_pin(auth.pin):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid PIN')
    token = create_token()
    set_auth_cookie(response, token)
    return {'token': token}


@router.post('/logout')
def logout(response: Response):
    clear_auth_cookie(response)
    return {'status': 'logged_out'}


@router.get('/status')
def auth_status(request: Request):
    return {'authenticated': is_authenticated(request)}
