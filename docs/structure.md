# Project Structure
- src/: Source code
  - core/: Core logic
  - modules/: Extensible modules (add new ones here)
- frontend/: Web interface
- config/: Settings
- tests/: Tests
- scripts/: Utilities
- logs/: Logs

## Extensibility
Add new modules in src/modules/ and import them in main.py as needed.

## TTS Recommendation
pyttsx3: Lightweight, offline, uses espeak on Linux, easy to integrate. Install via pip.