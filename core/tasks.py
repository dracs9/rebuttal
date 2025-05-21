import logging
import threading

from django.core.files.storage import default_storage

from .models import Speech
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
