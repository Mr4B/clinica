# app/middleware/audit_middleware.py
from fastapi import Request
from app.services.audit import set_audit_context
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.core import security
from jose import jwt, JWTError
import logging

logger = logging.getLogger(__name__)

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Estrai token dall'header Authorization
        auth_header = request.headers.get("Authorization")
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                # Decodifica JWT per estrarre info utente
                payload = jwt.decode(
                    token, 
                    settings.SECRET_KEY, 
                    algorithms=[security.ALGORITHM]
                )
                user_id = payload.get("sub")
                username = payload.get("username") or payload.get("email") or user_id
                
                # Setta contesto audit per questa request
                set_audit_context(
                    user_id=user_id,
                    username=username,
                    ip=request.client.host if request.client else None,
                    endpoint=f"{request.method} {request.url.path}"
                )
            except JWTError as e:
                logger.debug(f"JWT decode error in audit middleware: {e}")
                # Non bloccare la request, continua senza contesto audit
                pass
        
        response = await call_next(request)
        return response