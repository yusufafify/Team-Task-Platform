from hashlib import sha256

from rest_framework.throttling import SimpleRateThrottle


class LoginEmailThrottle(SimpleRateThrottle):
    """Caps guesses at one account across every address, for attacks spread over many."""

    scope = "login_email"

    def ident_for(self, request, email: str) -> str:
        return email

    def get_cache_key(self, request, view):
        email = request.data.get("email") if isinstance(request.data, dict) else None
        if not email:
            return None
        ident = self.ident_for(request, str(email).strip().lower())
        return self.cache_format % {
            "scope": self.scope,
            "ident": sha256(ident.encode()).hexdigest(),
        }


class LoginEmailAddressThrottle(LoginEmailThrottle):
    """Stops one address guessing at one account, without affecting the owner elsewhere."""

    scope = "login_email_address"

    def ident_for(self, request, email: str) -> str:
        return f"{email}|{self.get_ident(request)}"
