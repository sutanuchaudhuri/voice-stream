// Initialize socket.io connection
let socket = io();
// MediaRecorder instance for audio capture
let mediaRecorder;
// Array to store audio chunks
let audioChunks = [];
// Timeout for auto-stopping recording
let recordingTimeout;
// Last recorded audio blob
let lastAudioBlob;
// Auto-submission timer for streaming mode
let autoSubmissionTimer = null;
// Track if user is currently speaking
let isUserSpeaking = false;

// Progress bar control functions
function showProgressBar(message = 'Processing...', detail = 'Submitting question to AI model...') {
    const progressContainer = document.getElementById('processing-progress');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const progressDetail = document.getElementById('progress-detail');

    if (progressContainer) {
        progressContainer.style.display = '';
        progressText.textContent = message;
        progressDetail.textContent = detail;

        // Start with 0% and animate to 30%
        progressBar.style.width = '0%';
        progressBar.setAttribute('aria-valuenow', '0');

        // Animate to 30% over 0.5 seconds
        setTimeout(() => {
            progressBar.style.width = '30%';
            progressBar.setAttribute('aria-valuenow', '30');
        }, 100);
    }
}

function updateProgress(percentage, message, detail) {
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const progressDetail = document.getElementById('progress-detail');

    if (progressBar) {
        progressBar.style.width = percentage + '%';
        progressBar.setAttribute('aria-valuenow', percentage);

        if (message) progressText.textContent = message;
        if (detail) progressDetail.textContent = detail;
    }
}

function hideProgressBar() {
    const progressContainer = document.getElementById('processing-progress');
    const progressBar = document.getElementById('progress-bar');

    if (progressContainer && progressBar) {
        // Complete the progress bar first
        progressBar.style.width = '100%';
        progressBar.setAttribute('aria-valuenow', '100');

        // Hide after a brief delay
        setTimeout(() => {
            progressContainer.style.display = 'none';
            // Reset for next use
            progressBar.style.width = '0%';
            progressBar.setAttribute('aria-valuenow', '0');
        }, 500);
    }
}

// Toggle UI elements based on streaming checkbox
window.toggleStreamingUI = function() {
    const useStreaming = document.getElementById('use-streaming').checked;
    const autoSubmitGroup = document.getElementById('auto-submit-group');
    const questionBox = document.getElementById('question-box');
    const submitStreamingBtn = document.getElementById('submit-streaming-btn');

    document.getElementById('pause-interval-group').style.display = useStreaming ? '' : 'none';
    document.getElementById('stop-recording-btn').style.display = useStreaming ? 'none' : '';
    document.getElementById('pause-timer').innerText = '';

    // Show/hide auto-submit checkbox only in streaming mode
    if (autoSubmitGroup) {
        autoSubmitGroup.style.display = useStreaming ? '' : 'none';
    }

    // Update question box and submit button visibility based on streaming mode
    if (useStreaming) {
        questionBox.readOnly = false; // Make question box editable in streaming mode
        toggleAutoSubmit(); // Update submit button visibility
    } else {
        questionBox.readOnly = true; // Keep read-only in non-streaming voice mode
        if (submitStreamingBtn) {
            submitStreamingBtn.style.display = 'none';
        }
    }
};

// Call toggleStreamingUI on page load to set initial state
if (typeof window !== 'undefined') {
    window.addEventListener('DOMContentLoaded', function() {
        window.toggleStreamingUI();
        const pauseSlider = document.getElementById('pause-interval');
        const pauseValue = document.getElementById('pause-interval-value');
        if (pauseSlider && pauseValue) {
            pauseSlider.addEventListener('input', function() {
                pauseValue.textContent = parseFloat(pauseSlider.value).toFixed(1);
            });
        }

        // Set up recording timeout slider
        const timeoutSlider = document.getElementById('recording-timeout');
        const timeoutValue = document.getElementById('recording-timeout-value');
        if (timeoutSlider && timeoutValue) {
            timeoutSlider.addEventListener('input', function() {
                timeoutValue.textContent = timeoutSlider.value;
            });
        }
    });
}

// Toggle auto-submit functionality
window.toggleAutoSubmit = function() {
    const useStreaming = document.getElementById('use-streaming').checked;
    const autoSubmit = document.getElementById('auto-submit-toggle').checked;
    const submitStreamingBtn = document.getElementById('submit-streaming-btn');

    if (useStreaming && submitStreamingBtn) {
        // Show submit button only in streaming mode when auto-submit is OFF
        submitStreamingBtn.style.display = autoSubmit ? 'none' : '';
    }
};

// Start recording audio from the user's microphone
window.startRecording = function() {
    document.getElementById('recording-cue').style.display = 'block';
    audioChunks = [];
    const inputLanguage = document.getElementById('input-language');
    window._selectedLanguage = inputLanguage ? inputLanguage.value : 'en';
    const useStreaming = document.getElementById('use-streaming').checked;
    let pauseInterval = 1.0;
    if (useStreaming) {
        const intervalInput = document.getElementById('pause-interval');
        pauseInterval = parseFloat(intervalInput && intervalInput.value ? intervalInput.value : '1.0');
        if (isNaN(pauseInterval) || pauseInterval < 0.1) pauseInterval = 1.0;
    }
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            // Create a MediaRecorder for the audio stream
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.start();
            // On each available audio chunk
            mediaRecorder.ondataavailable = e => {
                if (e.data.size > 0) {
                    audioChunks.push(e.data);
                    if (useStreaming) {
                        // Send chunk to streaming endpoint in real time
                        sendAudioChunkStreaming(e.data);
                    }
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
            let silenceThreshold = 0.01; // Silence threshold (RMS)
            let silenceDuration = pauseInterval * 1000; // Use user value
            let timerInterval = null;

            // Timer update for pause detection
            function updatePauseTimer() {
                if (!silenceStart) {
                    document.getElementById('pause-timer').innerText = '';
                    return;
                }
                const elapsed = Date.now() - silenceStart;
                const left = Math.max(0, silenceDuration - elapsed);
                document.getElementById('pause-timer').innerText = `Pause auto-stop in ${(left/1000).toFixed(1)}s`;
            }

            // Function to check for silence in the audio stream
            function checkSilence() {
                analyser.getByteTimeDomainData(dataArray);
                let sumSquares = 0;
                for (let i = 0; i < dataArray.length; i++) {
                    let normalized = (dataArray[i] - 128) / 128;
                    sumSquares += normalized * normalized;
                }
                let rms = Math.sqrt(sumSquares / dataArray.length);
                if (rms < silenceThreshold) {
                    // User is not speaking
                    isUserSpeaking = false;

                    if (!silenceStart) silenceStart = Date.now();
                    updatePauseTimer();
                    if (Date.now() - silenceStart > silenceDuration) {
                        // Detected silence for required duration, stop recording
                        stream.getTracks().forEach(track => track.stop());
                        // Handle auto-stop for streaming mode
                        handleStreamingAutoStop();
                        audioContext.close();
                        document.getElementById('pause-timer').innerText = '';
                        if (timerInterval) clearInterval(timerInterval);
                        return;
                    }
                } else {
                    // User is speaking - cancel any pending auto-submission
                    isUserSpeaking = true;
                    if (autoSubmissionTimer) {
                        clearTimeout(autoSubmissionTimer);
                        autoSubmissionTimer = null;
                    }

                    silenceStart = null;
                    updatePauseTimer();
                }
                requestAnimationFrame(checkSilence);
            }
            checkSilence();

            // Timer for updating pause timer display
            if (useStreaming) {
                timerInterval = setInterval(updatePauseTimer, 100);
            }

            // Stop recording automatically after configurable timeout
            const timeoutSlider = document.getElementById('recording-timeout');
            const timeoutSeconds = timeoutSlider ? parseInt(timeoutSlider.value) : 60; // Default to 60 seconds

            recordingTimeout = setTimeout(() => {
                stream.getTracks().forEach(track => track.stop());
                if (useStreaming) {
                    handleStreamingAutoStop();
                } else {
                    window.stopRecording();
                }
                audioContext.close();
                document.getElementById('pause-timer').innerText = '';
                if (timerInterval) clearInterval(timerInterval);
            }, timeoutSeconds * 1000); // Convert seconds to milliseconds
        });
};

// Helper to get noise cancellation flag
function isNoiseCancellationEnabled() {
    const noiseToggle = document.getElementById('noise-cancel-toggle');
    return noiseToggle && noiseToggle.checked;
}

// Handle streaming auto-stop - submit question to LLM automatically only if auto-submit is enabled
function handleStreamingAutoStop() {
    document.getElementById('recording-cue').style.display = 'none';
    isUserSpeaking = false; // User stopped speaking

    // Clear any pending auto-submission timer since recording stopped
    if (autoSubmissionTimer) {
        clearTimeout(autoSubmissionTimer);
        autoSubmissionTimer = null;
    }

    // Get the current transcribed text from the question box
    const questionText = document.getElementById('question-box').value.trim();
    const autoSubmit = document.getElementById('auto-submit-toggle').checked;

    if (questionText) {
        if (autoSubmit) {
            // Set up immediate auto-submission since recording stopped
            setupAutoSubmissionTimer();
        } else {
            // Auto-submit is disabled - just show a message that transcription is complete
            document.getElementById('result').innerText = 'Transcription complete. Click "Submit Question" to get an answer.';
        }
    } else {
        document.getElementById('result').innerText = 'No text transcribed to process.';
    }
}

// Send a single audio chunk to the streaming endpoint
function sendAudioChunkStreaming(blob) {
    // Cancel any pending auto-submission since user is speaking
    if (autoSubmissionTimer) {
        clearTimeout(autoSubmissionTimer);
        autoSubmissionTimer = null;
    }

    // Mark user as speaking
    isUserSpeaking = true;

    const reader = new FileReader();
    reader.onload = function() {
        const base64data = reader.result.split(',')[1];
        fetch('/tts/stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                audio: base64data,
                language: window._selectedLanguage,
                noise_cancellation: isNoiseCancellationEnabled()
            })
        })
        .then(response => response.json())
        .then(data => {
            // Update the question box with partial transcription
            if (data && data.partial_text) {
                document.getElementById('question-box').value = data.partial_text;
                // Store the latest transcription for auto-submission
                window._latestStreamingText = data.partial_text;

                // Set up auto-submission timer if auto-submit is enabled
                setupAutoSubmissionTimer();
            }
        })
        .catch(err => {
            console.error('Streaming error:', err);
        });
    };
    reader.readAsDataURL(blob);
}

// Setup auto-submission timer for streaming mode
function setupAutoSubmissionTimer() {
    const autoSubmit = document.getElementById('auto-submit-toggle').checked;

    if (!autoSubmit) return;

    // Clear any existing timer
    if (autoSubmissionTimer) {
        clearTimeout(autoSubmissionTimer);
    }

    // Set new timer for 2 seconds
    autoSubmissionTimer = setTimeout(() => {
        const questionText = document.getElementById('question-box').value.trim();

        if (questionText && !isUserSpeaking) {
            // Auto-submit the transcribed question
            document.getElementById('result').innerText = 'Auto-submitting question...';
            document.getElementById('answer-box').value = ''; // Clear previous answer

            // Show progress bar for auto-submit
            showProgressBar('Processing your question...', 'Auto-submitting to AI model for analysis...');

            socket.emit('audio_blob', JSON.stringify({
                text: questionText,
                language: window._selectedLanguage || 'en',
                noise_cancellation: isNoiseCancellationEnabled()
            }));

            // Clear the timer
            autoSubmissionTimer = null;
        }
    }, 2000); // 2 seconds delay
}

// Stop recording and process the audio
window.stopRecording = function() {
    // Guard to prevent multiple calls
    if (window._isRecordingStopped) return;
    window._isRecordingStopped = true;
    document.getElementById('recording-cue').style.display = 'none';
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        clearTimeout(recordingTimeout);
        mediaRecorder.onstop = () => {
            // Combine all audio chunks into a single blob
            lastAudioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            let reader = new FileReader();
            reader.onload = function() {
                // Convert audio to base64 and emit to server via socket
                let base64data = btoa(String.fromCharCode(...new Uint8Array(reader.result)));
                const language = window._selectedLanguage || 'en';

                // Show progress bar for voice processing
                showProgressBar('Processing your voice...', 'Converting speech to text and generating response...');

                socket.emit('audio_blob', JSON.stringify({
                    audio: base64data,
                    language: language,
                    noise_cancellation: isNoiseCancellationEnabled()
                }));
                document.getElementById('result').innerText = 'Uploading audio...';
            };
            reader.readAsArrayBuffer(lastAudioBlob);
        };
    }
    // Reset guard after short delay to allow new recordings
    setTimeout(() => { window._isRecordingStopped = false; }, 2000);
};

// Play the last recorded audio
window.playAudio = function() {
    if (lastAudioBlob) {
        let audioURL = URL.createObjectURL(lastAudioBlob);
        let player = document.getElementById('audio-player');
        player.src = audioURL;
        player.style.display = 'block';
        player.play();
    }
};

// Submit streaming question manually
window.submitStreamingQuestion = function() {
    const questionText = document.getElementById('question-box').value.trim();

    if (!questionText) {
        document.getElementById('result').innerText = 'Please enter a question to submit.';
        return;
    }

    // Show progress bar for manual submission
    showProgressBar('Processing your question...', 'Submitting to AI model for analysis...');

    // Submit the question to LLM for answer generation
    document.getElementById('result').innerText = 'Processing question...';
    document.getElementById('answer-box').value = ''; // Clear previous answer

    socket.emit('audio_blob', JSON.stringify({
        text: questionText,
        language: window._selectedLanguage || 'en',
        noise_cancellation: isNoiseCancellationEnabled()
    }));
};

// Handle transcription updates from the server
socket.on('transcription_update', function(data) {
    console.log('[DEBUG] Received transcription_update event:', data);

    // Hide progress bar when we receive response
    hideProgressBar();

    if (data.error || data.answer === 'Error processing audio.') {
        document.getElementById('result').innerText = 'Error: Audio upload or transcription failed.';
    } else {
        document.getElementById('question-box').value = data.question || '';
        document.getElementById('answer-box').value = data.answer || '';
        document.getElementById('result').innerText = '';

        // Show audio controls when we have an answer
        if (data.answer) {
            document.querySelector('.audio-controls').style.display = 'block';
        }

        // Handle speaker diarization results
        if (data.diarization && Array.isArray(data.diarization) && data.diarization.length > 0) {
            displayDiarizationResults(data.diarization);
        }
    }
});

// Display diarization results (simplified for main page)
function displayDiarizationResults(diarizationData) {
    const resultDiv = document.getElementById('result');
    resultDiv.innerHTML = '<div class="alert alert-info">Speaker diarization completed! <a href="/diarization" target="_blank" class="btn btn-sm btn-primary">View Detailed Results</a></div>';

    // Store diarization data in sessionStorage for the separate page
    sessionStorage.setItem('diarizationResults', JSON.stringify(diarizationData));
}

// DOMContentLoaded: Setup UI event handlers and input mode switching
document.addEventListener('DOMContentLoaded', function() {
    // Input mode switching logic
    const inputMode = document.getElementById('input-mode');
    const startRecordingBtn = document.getElementById('start-recording-btn');
    const stopRecordingBtn = document.getElementById('stop-recording-btn');
    const questionBox = document.getElementById('question-box');
    const submitTextBtn = document.getElementById('submit-text-btn');

    function setInputMode(mode) {
        if (mode === 'voice') {
            startRecordingBtn.style.display = '';
            questionBox.readOnly = true;
            submitTextBtn.style.display = 'none';
            // Show/hide stop button based on streaming mode
            window.toggleStreamingUI();
        } else {
            startRecordingBtn.style.display = 'none';
            stopRecordingBtn.style.display = 'none';
            questionBox.readOnly = false;
            submitTextBtn.style.display = '';
        }
    }

    if (inputMode) {
        setInputMode(inputMode.value);
        inputMode.onchange = function() {
            setInputMode(inputMode.value);
        };
    }

    if (submitTextBtn) {
        submitTextBtn.onclick = function() {
            const question = questionBox.value.trim();
            const inputLanguage = document.getElementById('input-language');
            const language = inputLanguage ? inputLanguage.value : 'en';
            if (question) {
                // Show progress bar for text submission
                showProgressBar('Processing your question...', 'Submitting text question to AI model...');

                socket.emit('audio_blob', JSON.stringify({text: question, language: language}));
                document.getElementById('result').innerText = 'Submitting question...';
            }
        };
    }

    // TTS button functionality
    const ttsBtn = document.getElementById('tts-btn');
    const pauseAudioBtn = document.getElementById('pause-audio-btn');
    const ttsAudio = document.getElementById('tts-audio');

    if (ttsBtn && ttsAudio) {
        ttsBtn.onclick = async function() {
            const answer = document.getElementById('answer-box').value;
            if (answer) {
                ttsBtn.disabled = true;
                ttsBtn.innerHTML = '<span style="font-size:1.5em;">🔄</span>';
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
                pauseAudioBtn.innerHTML = '<span style="font-size:1.5em;">▶️</span>';
            } else {
                ttsAudio.play();
                pauseAudioBtn.innerHTML = '<span style="font-size:1.5em;">⏸️</span>';
            }
        };
    }
});
