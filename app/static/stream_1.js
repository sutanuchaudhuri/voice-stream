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

            // Silence detection using Web Audio API
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const source = audioContext.createMediaStreamSource(stream);
            const analyser = audioContext.createAnalyser();
            source.connect(analyser);
            analyser.fftSize = 2048;
            const dataArray = new Uint8Array(analyser.fftSize);
            let silenceStart = null;
            let silenceThreshold = 0.01; // Adjust as needed
            let silenceDuration = 1000; // ms

            function checkSilence() {
                analyser.getByteTimeDomainData(dataArray);
                // Calculate RMS (root mean square) volume
                let sumSquares = 0;
                for (let i = 0; i < dataArray.length; i++) {
                    let normalized = (dataArray[i] - 128) / 128;
                    sumSquares += normalized * normalized;
                }
                let rms = Math.sqrt(sumSquares / dataArray.length);
                if (rms < silenceThreshold) {
                    if (!silenceStart) silenceStart = Date.now();
                    if (Date.now() - silenceStart > silenceDuration) {
                        // Detected silence for required duration
                        stream.getTracks().forEach(track => track.stop());
                        window.stopRecording();
                        audioContext.close();
                        return;
                    }
                } else {
                    silenceStart = null;
                }
                requestAnimationFrame(checkSilence);
            }
            checkSilence();

            // Stop after 1 minute automatically
            recordingTimeout = setTimeout(() => {
                stream.getTracks().forEach(track => track.stop());
                window.stopRecording();
                audioContext.close();
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
                // Only process once, do not call reader.readAsArrayBuffer here!
                let base64data = btoa(String.fromCharCode(...new Uint8Array(reader.result)));
                console.log('[DEBUG] Emitting audio_blob event with base64 data of length:', base64data.length);
                socket.emit('audio_blob', base64data);
                document.getElementById('result').innerText = 'Uploading audio...';
            };
            // Only call readAsArrayBuffer once, outside of onload
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
        // Automatically play TTS audio for the answer
        const ttsAudio = document.getElementById('tts-audio');
        if (data.answer && ttsAudio) {
            const formData = new FormData();
            formData.append('text', data.answer);
            fetch('/tts', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) throw new Error('TTS request failed');
                return response.blob();
            })
            .then(audioBlob => {
                ttsAudio.src = URL.createObjectURL(audioBlob);
                ttsAudio.style.display = 'block';
                ttsAudio.play();
            })
            .catch(err => {
                console.error('Error streaming TTS audio:', err);
            });
        }
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const ttsBtn = document.getElementById('tts-btn');
    const pauseAudioBtn = document.getElementById('pause-audio-btn');
    const ttsAudio = document.getElementById('tts-audio');

    if (ttsBtn && ttsAudio) {
        ttsBtn.onclick = async function() {
            const answer = document.getElementById('answer-box').value;
            if (answer) {
                ttsBtn.disabled = true;
                ttsBtn.innerText = '🔄';
                ttsAudio.style.display = 'none';
                try {
                    const formData = new FormData();
                    formData.append('text', answer);
                    const response = await fetch('/tts', {
                        method: 'POST',
                        body: formData
                    });
                    if (!response.ok) throw new Error('TTS request failed');
                    const audioBlob = await response.blob();
                    ttsAudio.src = URL.createObjectURL(audioBlob);
                    ttsAudio.style.display = 'block';
                    ttsAudio.play();
                } catch (err) {
                    alert('Error streaming TTS audio: ' + err.message);
                } finally {
                    ttsBtn.disabled = false;
                    ttsBtn.innerHTML = '<span style="font-size:1.5em;">🔊</span>';
                }
            }
        };
    }

    if (pauseAudioBtn && ttsAudio) {
        pauseAudioBtn.onclick = function() {
            if (!ttsAudio.paused) {
                ttsAudio.pause();
            } else {
                ttsAudio.play();
            }
        };
    }
});













