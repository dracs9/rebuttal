from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.index, name="home"),
    path("register/", views.register, name="register"),
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page="core:home"), name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("speech/upload/", views.upload_speech, name="upload_speech"),
    path("speech/<int:speech_id>/", views.speech_detail, name="speech_detail"),
    path("speech/<int:speech_id>/analyze/", views.analyze_speech, name="analyze_speech"),
    path(
        "speech/<int:speech_id>/analysis-status/", views.get_analysis_status, name="analysis_status"
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
