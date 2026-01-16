# app/authentication.py
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from user.models import UserToken

class MultiTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Token "):
            return None

        key = auth.replace("Token ", "")

        try:
            token = UserToken.objects.select_related("user").get(key=key)
        except UserToken.DoesNotExist:
            raise AuthenticationFailed("Invalid token")

        return (token.user, token)
