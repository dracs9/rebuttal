from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator

from .models import Speech


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"class": "form-input"}))

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-input"}),
            "password1": forms.PasswordInput(attrs={"class": "form-input"}),
            "password2": forms.PasswordInput(attrs={"class": "form-input"}),
        }


class SpeechUploadForm(forms.ModelForm):
    class Meta:
        model = Speech
        fields = ["title", "audio_file"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter speech title",
                }
            ),
            "audio_file": forms.FileInput(
                attrs={
                    "class": "block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100",
                    "accept": "audio/mp3,audio/wav,audio/mpeg",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add validation for audio file formats
        self.fields["audio_file"].validators = [
            FileExtensionValidator(
                allowed_extensions=["mp3", "wav", "m4a"],
                message="Please upload an MP3, WAV, or M4A file.",
            )
        ]
        # Add help text
        self.fields["audio_file"].help_text = (
            "Supported formats: MP3, WAV, M4A. Maximum file size: 10MB."
        )
        # Add max file size validation
        self.fields["audio_file"].widget.attrs["accept"] = ".mp3,.wav,.m4a"
        self.fields["audio_file"].widget.attrs["max_length"] = 10 * 1024 * 1024  # 10MB

    def clean_audio_file(self):
        audio_file = self.cleaned_data.get("audio_file")
        if audio_file:
            if audio_file.size > 10 * 1024 * 1024:  # 10MB
                raise forms.ValidationError("File size must be no more than 10MB.")

        return audio_file
