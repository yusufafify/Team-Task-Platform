from django.urls import path

from apps.accounts import views

urlpatterns = [
    path("register/", views.RegisterView.as_view()),
    path("login/", views.LoginView.as_view()),
    path("refresh/", views.RefreshView.as_view()),
    path("logout/", views.LogoutView.as_view()),
    path("logout-all/", views.LogoutAllView.as_view()),
    path("mobile/login/", views.MobileLoginView.as_view()),
    path("mobile/refresh/", views.MobileRefreshView.as_view()),
    path("mobile/logout/", views.MobileLogoutView.as_view()),
    path("me/", views.MeView.as_view()),
]
