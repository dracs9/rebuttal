from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Speech(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="speeches")
    title = models.CharField(max_length=200)
    audio_file = models.FileField(upload_to="speeches/")
    upload_date = models.DateTimeField(default=timezone.now)
    transcript = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    error_message = models.TextField(blank=True, null=True)
    processing_started = models.DateTimeField(null=True, blank=True)
    processing_completed = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-upload_date"]

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    def start_processing(self):
        self.status = "processing"
        self.processing_started = timezone.now()
        self.save()

    def complete_processing(self, transcript):
        self.status = "completed"
        self.transcript = transcript
        self.processing_completed = timezone.now()
        self.save()

    def mark_failed(self, error_message):
        self.status = "failed"
        self.error_message = error_message
        self.processing_completed = timezone.now()
        self.save()


class SpeechAnalysis(models.Model):
    speech = models.OneToOneField(Speech, on_delete=models.CASCADE, related_name="analysis")
    structure_score = models.IntegerField(null=True, blank=True)
    argument_score = models.IntegerField(null=True, blank=True)
    persuasiveness_score = models.IntegerField(null=True, blank=True)
    rhetoric_score = models.IntegerField(null=True, blank=True)
    delivery_score = models.IntegerField(null=True, blank=True)
    feedback = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Speech analyses"

    def __str__(self):
        return f"Analysis for {self.speech.title}"

    @property
    def average_score(self):
        scores = [
            self.structure_score,
            self.argument_score,
            self.persuasiveness_score,
            self.rhetoric_score,
            self.delivery_score,
        ]
        valid_scores = [s for s in scores if s is not None]
        return sum(valid_scores) / len(valid_scores) if valid_scores else None
