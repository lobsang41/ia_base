// Basic chat functionality
function sendMessage() {
    var msg = document.getElementById('message').value;
    document.getElementById('chat-window').innerHTML += '<p>' + msg + '</p>';
    // TODO: Integrate with backend for TTS, etc.
    document.getElementById('message').value = '';
}