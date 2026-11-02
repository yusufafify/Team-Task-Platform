from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
)

from apps.accounts import services
from apps.accounts.authentication import REFRESH_COOKIE, clear_auth_cookies, set_auth_cookies
from apps.accounts.permissions import NoBrowser, TrustedOrigin
from apps.accounts.serializers import RegisterSerializer, UserSerializer
from apps.accounts.throttles import LoginEmailAddressThrottle, LoginEmailThrottle


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [TrustedOrigin]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "register"

    def perform_create(self, serializer):
        serializer.instance = services.register_user(**serializer.validated_data)


class LoginLimits:
    """Shared by both logins, so alternating between them buys no extra guesses."""

    throttle_classes = [LoginEmailAddressThrottle, ScopedRateThrottle, LoginEmailThrottle]
    throttle_scope = "login_ip"

    def check_throttles(self, request):
        # DRF counts a request against every throttle, even after one refuses it. Stopping at the
        # first refusal keeps one address from using up the limit shared by the whole account.
        for throttle in self.get_throttles():
            if not throttle.allow_request(request, self):
                self.throttled(request, throttle.wait())


class LoginView(LoginLimits, TokenObtainPairView):
    permission_classes = [TrustedOrigin]

    @extend_schema(responses=UserSerializer)
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response = Response(UserSerializer(serializer.user).data)
        set_auth_cookies(response, **serializer.validated_data)
        return response


class RefreshView(TokenRefreshView):
    permission_classes = [TrustedOrigin]

    @extend_schema(request=None, responses={204: None})
    def post(self, request, *args, **kwargs):
        refresh = request.COOKIES.get(REFRESH_COOKIE)
        if refresh is None:
            raise InvalidToken("No refresh token.")
        serializer = self.get_serializer(data={"refresh": refresh})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as error:
            raise InvalidToken(error.args[0]) from error
        # Failures above leave the cookies alone: another tab may have just rotated them.
        response = Response(status=status.HTTP_204_NO_CONTENT)
        set_auth_cookies(response, **serializer.validated_data)
        return response


class LogoutView(APIView):
    authentication_classes = []
    permission_classes = [TrustedOrigin]

    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        services.revoke_refresh_token(request.COOKIES.get(REFRESH_COOKIE))
        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_auth_cookies(response)
        return response


class LogoutAllView(APIView):
    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        services.revoke_all_tokens(request.user)
        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_auth_cookies(response)
        return response


class MobileLoginView(LoginLimits, TokenObtainPairView):
    permission_classes = [NoBrowser]


class MobileRefreshView(TokenRefreshView):
    permission_classes = [NoBrowser]


class MobileLogoutView(TokenBlacklistView):
    permission_classes = [NoBrowser]


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        return self.request.user
