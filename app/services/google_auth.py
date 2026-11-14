from fastapi import HTTPException
from app.core.config import settings
from app.services.security import valid_college_email


def verify_google_id_token(credential: str) -> dict:
    if not settings.google_client_id:
        raise HTTPException(503, "Google sign-in is not configured. Set GOOGLE_CLIENT_ID in .env.")
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests
    except ImportError as exc:
        raise HTTPException(503, "Google authentication dependencies are not installed.") from exc

    try:
        claims = id_token.verify_oauth2_token(
            credential,
            requests.Request(),
            settings.google_client_id,
        )
    except Exception as exc:
        # Never expose the token or its contents to the client/logs.
        raise HTTPException(401, "Invalid Google ID token. Check that the Google Web Client ID matches the one in .env.") from exc

    email = str(claims.get("email", "")).strip().lower()
    if not claims.get("email_verified"):
        raise HTTPException(403, "Google email is not verified")
    if claims.get("hd") != "iitdh.ac.in" or not valid_college_email(email):
        raise HTTPException(403, "Only verified iitdh.ac.in Google accounts are allowed")
    return claims
