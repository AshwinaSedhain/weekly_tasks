# Providing simple token-based authentication using a static bearer token.
# In production, replacing this with a proper JWT / OAuth2 implementation is recommended.
# Reading the token from the AUTH_TOKEN environment variable, falling back to "777777" for local development.

import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Loading the expected token from the environment at startup
EXPECTED_TOKEN: str = os.getenv("AUTH_TOKEN", "777777")

bearer_scheme = HTTPBearer(auto_error=False)


# Validating the Authorization: Bearer <token> header
# Raising HTTP 401 if the token is missing or incorrect
# Returning the token string on success
def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    if credentials is None or credentials.credentials != EXPECTED_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials
