let recognition;
let isRecording = false;

function initSpeechRecognition() {
    if (!('SpeechRecognition' in window) && !('webkitSpeechRecognition' in window)) {
        alert('Tu navegador no soporta reconocimiento de voz. Prueba con Chrome o Edge.');
        return;
    }
    recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'es-MX';
    recognition.interimResults = true;
    recognition.continuous = true;
    recognition.onresult = function(event) {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
            transcript += event.results[i][0].transcript + ' ';
        }
        transcript = transcript.trim();
        document.getElementById('transcription').innerText = transcript;
        if (!event.results[event.results.length - 1].isFinal) return;
        document.getElementById('message').value = transcript;
        sendMessage();
    };
    recognition.onerror = function(event) {
        console.error('Error en reconocimiento de voz:', event.error);
        toggleVoice();
    };
    recognition.onend = function() {
        isRecording = false;
        document.getElementById('voice-btn').classList.remove('recording');
        document.getElementById('voice-btn').innerText = '🎤 Iniciar Grabación';
    };
}

function toggleVoice() {
    if (!recognition) initSpeechRecognition();
    if (isRecording) {
        recognition.stop();
        document.getElementById('voice-btn').innerText = '🎤 Iniciar Grabación';
    } else {
        recognition.start();
        isRecording = true;
        document.getElementById('voice-btn').classList.add('recording');
        document.getElementById('voice-btn').innerText = '🔴 Detener Grabación';
    }
}

initSpeechRecognition();