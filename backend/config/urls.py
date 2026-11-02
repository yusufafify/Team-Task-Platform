"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path

from config import views

handler400 = "config.views.bad_request"
handler404 = "config.views.not_found"
handler500 = "config.views.server_error"

api_patterns = [
    path("auth/", include("apps.accounts.urls")),
    path("", include("apps.teams.urls")),
    path("", include("apps.tasks.urls")),
    path("", include("apps.chat.urls")),
    path("", include("apps.notifications.urls")),
    path("", include("apps.assistant.urls")),
    path("", include("apps.reports.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz", views.healthz),
    path("readyz", views.readyz),
    path("api/v1/", include(api_patterns)),
]
