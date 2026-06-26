"""Verify Google ID tokens server-side and extract the user profile."""
from dataclasses import dataclass

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.core.config import settings
from app.modules.auth.utils.exceptions import InvalidToken


@dataclass
class GoogleProfile:
    email: str
    first_name: str
    last_name: str
    email_verified: bool
    picture: str | None


class GoogleService:
    def verify(self, raw_id_token: str) -> GoogleProfile:
        if not settings.GOOGLE_CLIENT_ID:
            raise InvalidToken("Google login is not configured.")
        try:
            claims = google_id_token.verify_oauth2_token(
                raw_id_token,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )
        except ValueError as exc:
            raise InvalidToken("Invalid Google token.") from exc

        if claims.get("iss") not in (
            "accounts.google.com",
            "https://accounts.google.com",
        ):
            raise InvalidToken("Invalid Google token issuer.")

        email = claims.get("email")
        if not email:
            raise InvalidToken("Google token missing email.")

        return GoogleProfile(
            email=email,
            first_name=claims.get("given_name") or "",
            last_name=claims.get("family_name") or "",
            email_verified=bool(claims.get("email_verified", False)),
            picture=claims.get("picture"),
        )


google_service = GoogleService()
