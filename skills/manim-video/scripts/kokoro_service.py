"""manim-voiceover SpeechService for Kokoro, or any OpenAI-compatible /v1/audio/speech server.

    from kokoro_service import KokoroService   # on PYTHONPATH when rendered by render.sh
    class Explainer(VoiceoverScene):
        def construct(self):
            self.set_speech_service(KokoroService())
            with self.voiceover(text="A circle of radius one.") as tracker:
                self.play(Create(circle), run_time=tracker.duration)

Settings come from arguments or the environment (defaults in brackets):
KOKORO_BASE_URL [http://127.0.0.1:8880/v1], KOKORO_MODEL [kokoro], KOKORO_VOICE [af_heart],
KOKORO_API_KEY [none; sent as a Bearer token when set, never logged].
Clips are cached by manim-voiceover under media/voiceovers/, so re-renders do not call the server again.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from manim_voiceover.helper import remove_bookmarks
from manim_voiceover.services.base import SpeechService


class KokoroService(SpeechService):
    def __init__(self, voice: str | None = None, model: str | None = None, base_url: str | None = None,
                 speed: float = 1.0, response_format: str = "mp3", timeout: float = 120, **kwargs):
        self.voice = voice or os.environ.get("KOKORO_VOICE", "af_heart")
        self.model = model or os.environ.get("KOKORO_MODEL", "kokoro")
        self.base_url = (base_url or os.environ.get("KOKORO_BASE_URL", "http://127.0.0.1:8880/v1")).rstrip("/")
        self.speed, self.response_format, self.timeout = speed, response_format, timeout
        SpeechService.__init__(self, **kwargs)

    def generate_from_text(self, text, cache_dir=None, path=None, **kwargs):
        cache_dir = cache_dir or self.cache_dir
        input_text = remove_bookmarks(text)
        input_data = {"input_text": input_text, "service": "kokoro", "model": self.model,
                      "voice": self.voice, "speed": self.speed}
        cached = self.get_cached_result(input_data, cache_dir)
        if cached is not None:
            return cached
        audio_path = str(path) if path else f"{self.get_audio_basename(input_data)}.{self.response_format}"
        body = json.dumps({"model": self.model, "input": input_text, "voice": self.voice,
                           "response_format": self.response_format, "speed": self.speed}).encode()
        headers = {"Content-Type": "application/json"}
        if os.environ.get("KOKORO_API_KEY"):
            headers["Authorization"] = "Bearer " + os.environ["KOKORO_API_KEY"]
        request = urllib.request.Request(f"{self.base_url}/audio/speech", data=body, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                audio = response.read()
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError(f"Kokoro TTS request to {self.base_url}/audio/speech failed: {exc}") from None
        if len(audio) < 100:
            raise RuntimeError(f"Kokoro returned {len(audio)} bytes of audio for: {input_text[:60]!r}")
        Path(cache_dir, audio_path).write_bytes(audio)
        return {"input_text": text, "input_data": input_data, "original_audio": audio_path}
