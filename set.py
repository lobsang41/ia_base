import os
import sys
import subprocess

# Function to create directories and files for the project structure
def create_project_structure(project_name="MultiModuleChatProject", base_path="."):
    project_path = os.path.join(base_path, project_name)
    
    # Create main project directory
    os.makedirs(project_path, exist_ok=True)
    
    # Subdirectories
    directories = [
        "src",                  # Main source code
        "src/core",             # Core functionalities (e.g., chat logic)
        "src/modules",          # Extensible modules (AI, Arduino, OpenCV, etc.)
        "src/modules/ai",       # AI integration (optional connection)
        "src/modules/arduino",  # Arduino module
        "src/modules/opencv",   # OpenCV for camera, etc.
        "src/modules/tts_stt",  # Text-to-Speech and Speech-to-Text
        "frontend",             # Web frontend (using Flask for simplicity)
        "frontend/static",      # Static files (CSS, JS)
        "frontend/templates",   # HTML templates
        "config",               # Configuration files (e.g., env vars, settings)
        "tests",                # Unit tests
        "docs",                 # Documentation
        "scripts",              # Utility scripts (e.g., setup, run)
        "logs"                  # Log files
    ]
    
    for dir_path in directories:
        os.makedirs(os.path.join(project_path, dir_path), exist_ok=True)
    
    # Create essential files
    files_to_create = {
        os.path.join(project_path, "README.md"): "# MultiModuleChatProject\n\nA cross-platform Python project for text-to-voice chat with extensible modules.\n\n## Setup\nRun `python scripts/setup.py` for initial setup.\n\n## Run\nUse `python src/main.py` to start the application.",
        os.path.join(project_path, ".gitignore"): "venv/\n__pycache__/\n*.pyc\n*.pyo\n*.pyd\nlogs/\n.env",
        os.path.join(project_path, "requirements.txt"): "# Core dependencies\nflask\npyttsx3  # For TTS (lightweight, offline, works on Linux)\nspeechrecognition  # For STT (pair with pyttsx3)\npyaudio  # For microphone access (required for STT)\nopencv-python  # For camera\npyserial  # For Arduino\npython-dotenv  # For config\n\n# Optional: AI integration\ngroq  # Example AI API (replace with your choice)\n\n# WebSockets for real-time chat\nflask-socketio",
        os.path.join(project_path, "config/settings.py"): "# Configuration settings\nimport os\n\nBASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))\nSECRET_KEY = 'your-secret-key'\n\n# TTS Engine\nTTS_ENGINE = 'pyttsx3'  # Recommended: lightweight, offline, Linux-compatible",
        os.path.join(project_path, "src/main.py"): """# Main entry point for the application\nimport os\nimport sys\nfrom flask import Flask, render_template\nfrom dotenv import load_dotenv\n\nload_dotenv()  # Load environment variables\n\napp = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')\n\n@app.route('/')\ndef index():\n    return render_template('index.html')\n\nif __name__ == '__main__':\n    app.run(debug=True, host='0.0.0.0', port=5000)""",
        os.path.join(project_path, "frontend/templates/index.html"): """<!DOCTYPE html>\n<html>\n<head>\n    <title>Chat App</title>\n    <link rel="stylesheet" href="/static/style.css">\n</head>\n<body>\n    <h1>Text-to-Voice Chat</h1>\n    <div id="chat-window"></div>\n    <input type="text" id="message" placeholder="Type your message">\n    <button onclick="sendMessage()">Send</button>\n    <script src="/static/script.js"></script>\n</body>\n</html>""",
        os.path.join(project_path, "frontend/static/style.css"): "body { font-family: Arial; }\n#chat-window { border: 1px solid #ccc; height: 300px; overflow-y: scroll; }",
        os.path.join(project_path, "frontend/static/script.js"): "// Basic chat functionality\nfunction sendMessage() {\n    var msg = document.getElementById('message').value;\n    document.getElementById('chat-window').innerHTML += '<p>' + msg + '</p>';\n    // TODO: Integrate with backend for TTS, etc.\n    document.getElementById('message').value = '';\n}",
        os.path.join(project_path, "src/modules/tts_stt/tts.py"): """import pyttsx3\n\nclass TTS:\n    def __init__(self):\n        self.engine = pyttsx3.init()\n        self.engine.setProperty('rate', 150)  # Speed\n        self.engine.setProperty('volume', 1.0)  # Volume\n\n    def speak(self, text):\n        self.engine.say(text)\n        self.engine.runAndWait()\n\n# Usage example:\n# tts = TTS()\n# tts.speak('Hello, this is text to speech.')""",
        os.path.join(project_path, "src/modules/tts_stt/stt.py"): """import speech_recognition as sr\n\nclass STT:\n    def __init__(self):\n        self.recognizer = sr.Recognizer()\n\n    def listen(self):\n        with sr.Microphone() as source:\n            print("Listening...")\n            audio = self.recognizer.listen(source)\n            try:\n                return self.recognizer.recognize_google(audio)\n            except sr.UnknownValueError:\n                return "Could not understand audio"\n            except sr.RequestError:\n                return "API unavailable"\n\n# Usage example:\n# stt = STT()\n# text = stt.listen()\n# print(text)""",
        os.path.join(project_path, "scripts/run.sh"): "#!/bin/bash\n# Cross-platform run script\npython src/main.py",
        os.path.join(project_path, "scripts/setup.py"): """# Additional setup script (e.g., install dependencies)\nimport subprocess\nimport sys\n\ndef install_requirements():\n    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])\n\nif __name__ == '__main__':\n    install_requirements()""",
        os.path.join(project_path, "docs/structure.md"): "# Project Structure\n- src/: Source code\n  - core/: Core logic\n  - modules/: Extensible modules (add new ones here)\n- frontend/: Web interface\n- config/: Settings\n- tests/: Tests\n- scripts/: Utilities\n- logs/: Logs\n\n## Extensibility\nAdd new modules in src/modules/ and import them in main.py as needed.\n\n## TTS Recommendation\npyttsx3: Lightweight, offline, uses espeak on Linux, easy to integrate. Install via pip."
    }
    
    for file_path, content in files_to_create.items():
        with open(file_path, "w") as f:
            f.write(content)
    
    # Make run.sh executable (cross-platform check)
    if sys.platform != "win32":
        os.chmod(os.path.join(project_path, "scripts/run.sh"), 0o755)
    
    # Initialize git (optional, but good for version control)
    try:
        subprocess.run(["git", "init", project_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("Git repository initialized.")
    except Exception:
        print("Git not found or error initializing repo. Skipping.")
    
    print(f"Project '{project_name}' created successfully at {project_path}.")
    print("To install dependencies, run: python scripts/setup.py")
    print("To start the app, run: python src/main.py (or ./scripts/run.sh on Unix)")
    print("\nKey Features:")
    print("- Cross-platform: Uses Python standard libs and os-agnostic code.")
    print("- Web Frontend: Basic Flask app with HTML/JS for chat interface.")
    print("- TTS/STT: pyttsx3 for TTS (lightweight, offline, Linux-compatible with espeak). speech_recognition for STT (uses microphone via pyaudio).")
    print("- Extensible: Add modules like Arduino (pyserial), OpenCV (camera access), AI (e.g., connect to Grok API).")
    print("- Linux Support: Microphone/camera via pyaudio/OpenCV; ensure permissions (e.g., add user to audio/video groups).")
    print("\nNext Steps: Implement chat logic in src/core/, integrate modules in main.py.")

# Run the setup
if __name__ == "__main__":
    create_project_structure()