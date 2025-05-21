import json
from typing import Any, Dict, Optional

import requests
from django.conf import settings


class OllamaService:
    BASE_URL = "http://localhost:11434/api"
    MODEL = "mistral"

    @classmethod
    def analyze_speech(cls, transcript: str) -> Dict[str, Any]:
        """
        Analyze a speech transcript using Ollama's Mistral model.
        Returns a dictionary containing analysis scores and feedback.
        """
        prompt = f"""Analyze the following debate speech. Evaluate and provide scores (1-10) for each category:

Structure (intro, body, conclusion)
Argument clarity and logic
Persuasiveness
Use of rhetorical techniques
Delivery (clarity, pace)

Then give detailed feedback with improvement tips.

Format your response as JSON with the following structure:
{{
    "structure_score": <score>,
    "argument_score": <score>,
    "persuasiveness_score": <score>,
    "rhetoric_score": <score>,
    "delivery_score": <score>,
    "feedback": "<detailed feedback>"
}}

Speech transcript:
{transcript}

Respond only with the JSON object, no additional text."""

        try:
            response = requests.post(
                f"{cls.BASE_URL}/generate",
                json={"model": cls.MODEL, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()

            # Extract the JSON response from the model's output
            result = response.json()
            analysis_text = result.get("response", "")

            # Find the JSON object in the response
            try:
                # Try to find JSON-like content between curly braces
                start_idx = analysis_text.find("{")
                end_idx = analysis_text.rfind("}") + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = analysis_text[start_idx:end_idx]
                    analysis = json.loads(json_str)
                else:
                    raise ValueError("No JSON object found in response")

                # Validate and normalize scores
                for key in [
                    "structure_score",
                    "argument_score",
                    "persuasiveness_score",
                    "rhetoric_score",
                    "delivery_score",
                ]:
                    if key in analysis:
                        score = analysis[key]
                        if isinstance(score, (int, float)):
                            analysis[key] = max(1, min(10, int(score)))
                        else:
                            analysis[key] = None

                return analysis

            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse model response as JSON: {e}")

        except requests.RequestException as e:
            raise ConnectionError(f"Failed to connect to Ollama service: {e}")
        except Exception as e:
            raise Exception(f"Error analyzing speech: {e}")

    @classmethod
    def is_available(cls) -> bool:
        """Check if Ollama service is available"""
        try:
            response = requests.get(f"{cls.BASE_URL}/tags")
            return response.status_code == 200
        except requests.RequestException:
            return False
