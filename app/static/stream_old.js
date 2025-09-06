let socket = io();
let mediaRecorder;
let audioChunks = [];
let recordingTimeout;
let lastAudioBlob;

window.startRecording = function() {
    document.getElementById('recording-cue').style.display = 'block';
    audioChunks = [];
    document.getElementById('playback-btn').style.display = 'none';
    document.getElementById('audio-player').style.display = 'none';
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.start();
            mediaRecorder.ondataavailable = e => {
                if (e.data.size > 0) {
                    audioChunks.push(e.data);
                }
            };
            // Stop after 1 minute automatically
            recordingTimeout = setTimeout(() => {
                window.stopRecording();
            }, 60000);
        });
};

window.stopRecording = function() {
    document.getElementById('recording-cue').style.display = 'none';
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        clearTimeout(recordingTimeout);
        mediaRecorder.onstop = () => {
            lastAudioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            let reader = new FileReader();
            reader.onload = function() {
                let base64data = btoa(String.fromCharCode(...new Uint8Array(reader.result)));
                console.log('[DEBUG] Emitting audio_blob event with base64 data of length:', base64data.length);
                socket.emit('audio_blob', base64data);
                document.getElementById('result').innerText = 'Uploading audio...';
            };
            reader.readAsArrayBuffer(lastAudioBlob);
            document.getElementById('playback-btn').style.display = 'inline-block';
        };
    }
};

window.playAudio = function() {
    if (lastAudioBlob) {
        let audioURL = URL.createObjectURL(lastAudioBlob);
        let player = document.getElementById('audio-player');
        player.src = audioURL;
        player.style.display = 'block';
        player.play();
    }
};

socket.on('transcription_update', function(data) {
    console.log('[DEBUG] Received transcription_update event:', data);
    if (data.answer === 'Error processing audio.') {
        document.getElementById('result').innerText = 'Error: Audio upload or transcription failed.';
    } else {
        document.getElementById('question-box').value = data.question || '';
        document.getElementById('answer-box').value = data.answer || '';
        document.getElementById('result').innerText = '';
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const speakBtn = document.getElementById('speak-btn');
    const pauseBtn = document.getElementById('pause-btn');
    let currentUtterance = null;

    if (speakBtn) {
        speakBtn.onclick = function() {
            const answer = document.getElementById('answer-box').value;
            if (answer) {
                if (window.speechSynthesis.speaking) {
                    window.speechSynthesis.cancel();
                }
                currentUtterance = new SpeechSynthesisUtterance(answer);
                currentUtterance.lang = 'en-US';
                window.speechSynthesis.speak(currentUtterance);
            }
        };
    }

    if (pauseBtn) {
        pauseBtn.onclick = function() {
            if (window.speechSynthesis.speaking && !window.speechSynthesis.paused) {
                window.speechSynthesis.pause();
            } else if (window.speechSynthesis.paused) {
                window.speechSynthesis.resume();
            }
        };
    }
});













