from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts import services
from apps.accounts.serializers import RegisterSerializer, UserSerializer
from apps.accounts.throttles import LoginEmailAddressThrottle, LoginEmailThrottle


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "register"

    def perform_create(self, serializer):
        serializer.instance = services.register_user(**serializer.validated_data)


class LoginView(TokenObtainPairView):
    throttle_classes = [LoginEmailAddressThrottle, ScopedRateThrottle, LoginEmailThrottle]
    throttle_scope = "login_ip"

    def check_throttles(self, request):
        # DRF counts a request against every throttle, even after one refuses it. Stopping at the
        # first refusal keeps one address from using up the limit shared by the whole account.
        for throttle in self.get_throttles():
            if not throttle.allow_request(request, self):
                self.throttled(request, throttle.wait())


class LogoutAllView(APIView):
    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        services.revoke_all_tokens(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        return self.request.user
