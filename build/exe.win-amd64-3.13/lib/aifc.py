# Minimal aifc stub to satisfy imports in frozen builds where stdlib `aifc` is missing.
# This provides a very small subset of functionality and defers to the `wave` module
# for basic open/read when possible. It's intentionally minimal — full AIFF support
# is not required for typical speech recognition startup.

class Error(Exception):
    pass

try:
    import wave as _wave

    def open(file, mode='rb'):
        return _wave.open(file, mode)

    # expose a minimal interface
    AudioFile = _wave.Wave_read
except Exception:
    def open(file, mode='rb'):
        raise ImportError("aifc functionality not available in this build")

    AudioFile = None
