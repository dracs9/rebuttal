from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from .forms import SpeechUploadForm, UserRegistrationForm
from .models import Speech

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
    speeches = Speech.objects.filter(user=request.user).order_by("-created_at")[:5]
    return render(
        request,
        "dashboard.html",
        {
            "speeches": speeches,
        },
    )


@login_required
def upload_speech(request):
    if request.method == "POST":
        form = SpeechUploadForm(request.POST, request.FILES)
        if form.is_valid():
            speech = form.save(commit=False)
            speech.user = request.user
            speech.save()
            messages.success(request, "Speech uploaded successfully! We'll analyze it shortly.")
            return redirect("speech_detail", speech_id=speech.id)
    else:
        form = SpeechUploadForm()
    return render(request, "core/upload_speech.html", {"form": form})


@login_required
def speech_detail(request, speech_id):
    speech = get_object_or_404(Speech, id=speech_id, user=request.user)
    return render(request, "core/speech_detail.html", {"speech": speech})
