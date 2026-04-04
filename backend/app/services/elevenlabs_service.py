import os
from elevenlabs.client import ElevenLabs
from app.core.config import settings
from app.services.ai_service import analyze_text_with_ai

class ElevenLabsService:
    @staticmethod
    async def analyze_audio_conversation(file_path: str):
        """
        1. Uses ElevenLabs Speech-to-Text to transcribe the audio.
        2. Uses Gemini to analyze the transcript for 'Fumbling', 'Bad English', and 'Scam Intent'.
        """
        if not settings.ELEVENLABS_API_KEY:
            return []

        client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)

        try:
            # 1. Transcribe the audio file using ElevenLabs Scribe
            with open(file_path, "rb") as audio_file:
                transcription = client.speech_to_text.convert(
                    file=audio_file,
                    model_id="scribe_v1",
                    tag_audio_events=True
                )
            
            transcript_text = transcription.text
            
            # 2. Analyze the transcript using analyze_text_with_ai
            # We wrap the transcript in a context that the AI service will understand
            context_text = f"Audio Transcript from a job-related call: {transcript_text}"
            ai_res = analyze_text_with_ai(context_text)
            
            findings = []
            if isinstance(ai_res, dict) and "findings" in ai_res:
                findings = ai_res["findings"]
                # Mark these as audio-specific findings
                for f in findings:
                    f["message"] = f"[Audio Analysis] {f['message']}"
            
            return findings

        except Exception as e:
            print(f"ElevenLabs Analysis Error: {e}")
            return []
