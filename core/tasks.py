import logging
import threading

from django.core.files.storage import default_storage
from django.utils import timezone

from .models import Speech, SpeechAnalysis
from .services import OllamaService
from .utils import process_speech_with_whisper

logger = logging.getLogger(__name__)


def process_speech_background(speech_id: int):
    """
    Process speech in background thread
    """
    try:
        speech = Speech.objects.get(id=speech_id)
        logger.info(f"Starting to process speech {speech_id}")

        # Skip if already processed or processing
        if speech.status in ["completed", "processing"]:
            logger.info(f"Speech {speech_id} is already processed or processing")
            return

        # Mark as processing
        speech.start_processing()
        logger.info(f"Got speech file path for {speech_id}")

        # Get the full path to the audio file
        audio_path = default_storage.path(speech.audio_file.name)
        logger.info(f"Processing speech {speech_id} with Whisper")

        # Process with Whisper
        transcript = process_speech_with_whisper(audio_path)
        logger.info(f"Successfully processed speech {speech_id}")

        # Save results
        speech.complete_processing(transcript)

    except Speech.DoesNotExist:
        logger.error(f"Speech {speech_id} not found")
    except Exception as e:
        logger.error(f"Unexpected error processing speech {speech_id}: {str(e)}")
        if speech:
            speech.mark_failed(str(e))


def process_speech_async(speech_id: int):
    """
    Start speech processing in a background thread
    """
    logger.info(f"Starting async processing for speech {speech_id}")
    thread = threading.Thread(target=process_speech_background, args=(speech_id,))
    thread.daemon = True
    thread.start()


def analyze_speech_with_ai(speech_id: int) -> None:
    """
    Analyze a speech transcript using Ollama AI and save the results.
    """
    try:
        speech = Speech.objects.get(id=speech_id)

        if not speech.transcript:
            raise ValueError("Speech has no transcript to analyze")

        if not OllamaService.is_available():
            raise ConnectionError("Ollama service is not available")

        # Get AI analysis
        analysis_data = OllamaService.analyze_speech(speech.transcript)

        # Create or update analysis
        analysis, created = SpeechAnalysis.objects.update_or_create(
            speech=speech,
            defaults={
                "structure_score": analysis_data.get("structure_score"),
                "argument_score": analysis_data.get("argument_score"),
                "persuasiveness_score": analysis_data.get("persuasiveness_score"),
                "rhetoric_score": analysis_data.get("rhetoric_score"),
                "delivery_score": analysis_data.get("delivery_score"),
                "feedback": analysis_data.get("feedback", ""),
            },
        )

        logger.info(f"Successfully analyzed speech {speech_id}")

    except Speech.DoesNotExist:
        logger.error(f"Speech {speech_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error analyzing speech {speech_id}: {str(e)}")
        raise
