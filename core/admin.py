from django.contrib import admin

from core.models import Speech, SpeechAnalysis

# Register your models here.
admin.site.register([Speech, SpeechAnalysis])