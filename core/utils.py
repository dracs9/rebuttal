import logging
import os
import subprocess
from pathlib import Path

import whisper
from django.conf import settings

logger = logging.getLogger(__name__)


def check_ffmpeg() -> bool:
    """
    Check if FFmpeg is available
    """
    try:
        ffmpeg_path = os.path.join(settings.BASE_DIR, "venv", "Scripts", "ffmpeg.exe")
        logger.info(f"Checking FFmpeg at: {ffmpeg_path}")

        if not os.path.exists(ffmpeg_path):
            logger.error(f"FFmpeg not found at: {ffmpeg_path}")
            return False

        result = subprocess.run([ffmpeg_path, "-version"], capture_output=True, text=True)
        is_available = result.returncode == 0
        logger.info(f"FFmpeg is {'available' if is_available else 'not available'}")
        return is_available
    except Exception as e:
        logger.error(f"Error checking FFmpeg: {str(e)}")
        return False


def process_speech_with_whisper(audio_path: str) -> str:
    """
    Process audio file with Whisper using Python API
    """
    try:
        # Check FFmpeg availability first
        if not check_ffmpeg():
            raise Exception(
                "FFmpeg is not available. Please install FFmpeg to process audio files."
            )

        # Convert to absolute path and normalize for Windows
        audio_path = str(Path(audio_path).resolve())
        logger.info(f"Processing audio file at absolute path: {audio_path}")

        # Ensure the audio file exists
        if not os.path.exists(audio_path):
            logger.error(f"Audio file not found at path: {audio_path}")
            logger.error(f"Current working directory: {os.getcwd()}")
            logger.error(f"Directory contents: {os.listdir(os.path.dirname(audio_path))}")
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(f"Loading Whisper model")
        # Load the Whisper model
        model = whisper.load_model("base")
        logger.info("Model loaded successfully")

        logger.info(f"Starting transcription of: {audio_path}")
        # Transcribe the audio
        result = model.transcribe(audio_path, language="en", fp16=False)  # Use CPU
        logger.info("Transcription completed successfully")

        # Get the transcript
        transcript = result["text"].strip()
        logger.info("Transcript extracted successfully")
        return transcript

    except Exception as e:
        logger.error(f"Error processing speech: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        raise Exception(f"Error processing speech: {str(e)}")


def get_whisper_status() -> bool:
    """
    Check if Whisper and FFmpeg are available
    """
    try:
        logger.info("Checking Whisper and FFmpeg availability")
        # Check FFmpeg first
        if not check_ffmpeg():
            logger.error("FFmpeg is not available")
            return False

        # Try to load the model to verify it's working
        model = whisper.load_model("base")
        is_available = model is not None
        logger.info(f"Whisper is {'available' if is_available else 'not available'}")
        return is_available
    except Exception as e:
        logger.error(f"Error checking Whisper status: {str(e)}")
        return False
