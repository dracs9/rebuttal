import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from .forms import SpeechUploadForm, UserRegistrationForm
from .models import Speech
from .tasks import process_speech_async
from .utils import get_whisper_status

logger = logging.getLogger(__name__)

# Create your views here.


def index(request):
    return render(request, "core/index.html")


class CustomLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("dashboard")


def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful! Welcome to Debate Coach AI.")
            return redirect("dashboard")
    else:
        form = UserRegistrationForm()
    return render(request, "registration/register.html", {"form": form})


@login_required
def dashboard(request):
    speeches = Speech.objects.filter(user=request.user).order_by("-upload_date")[:5]
    return render(request, "dashboard.html", {"speeches": speeches})


@login_required
def upload_speech(request):
    if request.method == "POST":
        form = SpeechUploadForm(request.POST, request.FILES)
        if form.is_valid():
            logger.info("Form is valid, checking Whisper status")
            if not get_whisper_status():
                logger.error("Whisper is not available")
                messages.error(
                    request, "Speech processing is currently unavailable. Please try again later."
                )
                return redirect("dashboard")

            try:
                speech = form.save(commit=False)
                speech.user = request.user
                speech.save()
                logger.info(f"Speech saved with ID: {speech.pk}")
                logger.info(f"Audio file path: {speech.audio_file.path}")
                logger.info(f"Audio file URL: {speech.audio_file.url}")
                logger.info(f"Audio file name: {speech.audio_file.name}")

                process_speech_async(speech.pk)
                logger.info(f"Started processing speech {speech.pk}")

                messages.success(
                    request, "Speech uploaded successfully. Processing will begin shortly."
                )
                return redirect("speech_detail", speech_id=speech.pk)
            except Exception as e:
                logger.error(f"Error saving speech: {str(e)}")
                logger.error(f"Error type: {type(e)}")
                import traceback

                logger.error(f"Traceback: {traceback.format_exc()}")
                messages.error(request, "Error uploading speech. Please try again.")
        else:
            logger.error(f"Form errors: {form.errors}")
            messages.error(request, "Please correct the errors below.")
    else:
        form = SpeechUploadForm()

    return render(
        request,
        "core/upload_speech.html",
        {"form": form, "whisper_available": get_whisper_status()},
    )


@login_required
def speech_detail(request, speech_id):
    speech = get_object_or_404(Speech, id=speech_id, user=request.user)
    if speech.status == "pending":
        process_speech_async(speech.pk)
    return render(request, "core/speech_detail.html", {"speech": speech})


@login_required
def speech_status(request, speech_id):
    speech = get_object_or_404(Speech, id=speech_id, user=request.user)
    return JsonResponse(
        {
            "status": speech.status,
            "transcript": speech.transcript if speech.status == "completed" else None,
            "error": speech.error_message if speech.status == "failed" else None,
        }
    )
