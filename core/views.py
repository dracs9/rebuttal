import logging
import threading

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from .forms import SpeechUploadForm, UserRegistrationForm
from .models import Speech, SpeechAnalysis
from .services import OllamaService
from .tasks import analyze_speech_with_ai, process_speech_async
from .utils import get_whisper_status

logger = logging.getLogger(__name__)

# Create your views here.


def index(request):
    return render(request, "core/index.html")


class CustomLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("core:dashboard")


def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful! Welcome to Debate Coach AI.")
            return redirect("core:dashboard")
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
                return redirect("core:dashboard")

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
                return redirect("core:speech_detail", speech_id=speech.pk)
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
    analysis = getattr(speech, "analysis", None)

    context = {
        "speech": speech,
        "analysis": analysis,
        "ollama_available": OllamaService.is_available(),
    }
    return render(request, "core/speech_detail.html", context)


@login_required
def analyze_speech(request, speech_id):
    speech = get_object_or_404(Speech, id=speech_id, user=request.user)

    if not speech.transcript:
        messages.error(request, "Cannot analyze speech without transcript")
        return redirect("core:speech_detail", speech_id=speech_id)

    if not OllamaService.is_available():
        messages.error(request, "Ollama service is not available. Please make sure it's running.")
        return redirect("core:speech_detail", speech_id=speech_id)

    try:
        # Run analysis in a background thread
        thread = threading.Thread(target=analyze_speech_with_ai, args=(speech.id,))
        thread.daemon = True
        thread.start()

        messages.success(
            request, "Speech analysis started. Please refresh the page in a few moments."
        )
    except Exception as e:
        messages.error(request, f"Error starting analysis: {str(e)}")

    return redirect("core:speech_detail", speech_id=speech_id)


@login_required
def get_analysis_status(request, speech_id):
    speech = get_object_or_404(Speech, id=speech_id, user=request.user)
    analysis = getattr(speech, "analysis", None)

    if analysis:
        return JsonResponse(
            {
                "status": "completed",
                "analysis": {
                    "structure_score": analysis.structure_score,
                    "argument_score": analysis.argument_score,
                    "persuasiveness_score": analysis.persuasiveness_score,
                    "rhetoric_score": analysis.rhetoric_score,
                    "delivery_score": analysis.delivery_score,
                    "average_score": analysis.average_score,
                    "feedback": analysis.feedback,
                    "created_at": analysis.created_at.isoformat(),
                },
            }
        )

    return JsonResponse({"status": "pending"})
