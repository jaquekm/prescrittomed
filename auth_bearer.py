import jwt
from jwt import PyJWKClient
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer

# --- AQUI ESTÁ A CORREÇÃO ---
# Em vez de tentar ler do .env (que estava vindo None), 
# vamos colocar o link direto para garantir que funciona.
SUPABASE_URL = "https://jdazginfmfeqmmstkjtq.supabase.co"

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials = await super(JWTBearer, self).__call__(request)
        if not credentials:
            raise HTTPException(status_code=403, detail="Não autenticado.")
        
        token = credentials.credentials
        
        if not self.verify_jwt(token):
            raise HTTPException(status_code=403, detail="Token inválido ou expirado")
        
        return token

    def verify_jwt(self, token: str) -> bool:
        try:
            # Monta a URL das chaves (JWKS)
            jwks_url = f"{SUPABASE_URL}/rest/v1/auth/jwks"
            
            # O cliente baixa as chaves dessa URL
            jwks_client = PyJWKClient(jwks_url)
            
            # Descobre a chave de assinatura
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            
            # Decodifica e valida
            jwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256", "RS256"],
                audience="authenticated",
                options={"verify_exp": True}
            )
            return True
        except Exception as e:
            # Esse print vai aparecer no terminal se der erro de novo
            print(f"❌ ERRO AO VALIDAR TOKEN: {e}")
            return False