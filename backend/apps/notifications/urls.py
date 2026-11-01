from django.urls import path
from rest_framework.routers import SimpleRouter

from apps.notifications import views

router = SimpleRouter()
router.register("notifications", views.NotificationViewSet)

urlpatterns = [
    *router.urls,
    path("device-tokens/", views.DeviceTokenCreateView.as_view()),
    path("device-tokens/<str:token>/", views.DeviceTokenDetailView.as_view()),
]
