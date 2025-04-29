// Main JavaScript for Mental Health Support application

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    
    // Initialize popovers
    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
    const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
    
    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        document.querySelectorAll('.alert').forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Handle voice recording functionality if on a conversation page
    setupVoiceRecording();
    
    // Handle mood selection if on a mood tracking page
    setupMoodSelection();
    
    // Initialize charts if on dashboard
    initCharts();
});

// Setup voice recording functionality
function setupVoiceRecording() {
    const recordButton = document.getElementById('recordButton');
    const stopButton = document.getElementById('stopButton');
    const playButton = document.getElementById('playButton');
    const messageInput = document.getElementById('messageInput');
    
    if (!recordButton || !stopButton || !playButton) {
        return; // Not on a page with voice controls
    }
    
    let mediaRecorder;
    let audioChunks = [];
    let audioBlob;
    let audioUrl;
    
    // Handle record button click
    recordButton.addEventListener('click', function() {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                recordButton.classList.add('recording');
                stopButton.disabled = false;
                recordButton.disabled = true;
                playButton.disabled = true;
                
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];
                
                mediaRecorder.addEventListener('dataavailable', event => {
                    audioChunks.push(event.data);
                });
                
                mediaRecorder.addEventListener('stop', () => {
                    const tracks = stream.getTracks();
                    tracks.forEach(track => track.stop());
                    
                    audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    audioUrl = URL.createObjectURL(audioBlob);
                    playButton.disabled = false;
                    
                    // If WebSocket connection exists, send the audio
                    if (window.conversationSocket && window.conversationSocket.readyState === WebSocket.OPEN) {
                        sendVoiceMessage(audioBlob);
                    }
                });
                
                mediaRecorder.start();
            })
            .catch(error => console.error('Error accessing microphone:', error));
    });
    
    // Handle stop button click
    stopButton.addEventListener('click', function() {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
            recordButton.classList.remove('recording');
            stopButton.disabled = true;
            recordButton.disabled = false;
        }
    });
    
    // Handle play button click
    playButton.addEventListener('click', function() {
        if (audioUrl) {
            const audio = new Audio(audioUrl);
            audio.play();
        }
    });
    
    // Setup WebSocket connection if conversation_id exists
    const conversationId = document.getElementById('conversation-id')?.value;
    if (conversationId) {
        setupWebSocketConnection(conversationId);
    }
}

// Setup WebSocket connection for real-time voice chat
function setupWebSocketConnection(conversationId) {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/conversations/${conversationId}/`;
    
    window.conversationSocket = new WebSocket(wsUrl);
    
    window.conversationSocket.onopen = function(e) {
        console.log('WebSocket connection established');
    };
    
    window.conversationSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        
        if (data.type === 'assistant_response') {
            // Display assistant message
            addMessage(data.message.content, 'assistant');
            
            // Play voice response if available
            if (data.message.voice_url) {
                const audio = new Audio(data.message.voice_url);
                audio.play();
            }
        } else if (data.type === 'error') {
            console.error('Error from server:', data.message);
            showAlert(data.message, 'danger');
        }
    };
    
    window.conversationSocket.onclose = function(e) {
        console.log('WebSocket connection closed');
    };
    
    window.conversationSocket.onerror = function(e) {
        console.error('WebSocket error:', e);
        showAlert('연결 오류가 발생했습니다. 페이지를 새로고침해 주세요.', 'danger');
    };
    
    // Set up ping interval to keep connection alive
    setInterval(function() {
        if (window.conversationSocket && window.conversationSocket.readyState === WebSocket.OPEN) {
            window.conversationSocket.send(JSON.stringify({ type: 'ping' }));
        }
    }, 30000); // Send ping every 30 seconds
}

// Send voice message through WebSocket
function sendVoiceMessage(audioBlob) {
    const reader = new FileReader();
    reader.readAsDataURL(audioBlob);
    reader.onloadend = function() {
        const base64data = reader.result;
        const voiceId = document.getElementById('voiceSelect')?.value || 'default';
        
        window.conversationSocket.send(JSON.stringify({
            type: 'voice_end',
            audio_data: base64data,
            voice_id: voiceId
        }));
        
        // Display user message (placeholder until transcription comes back)
        addMessage('🎤 음성 메시지 전송 중...', 'user');
        
        // Show processing indicator
        const chatMessages = document.querySelector('.chat-messages');
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    };
}

// Send text message through WebSocket
function sendTextMessage(text) {
    if (!text.trim()) return;
    
    const voiceId = document.getElementById('voiceSelect')?.value || 'default';
    
    window.conversationSocket.send(JSON.stringify({
        type: 'text_message',
        message: text,
        voice_id: voiceId,
        generate_voice: true
    }));
    
    // Display user message
    addMessage(text, 'user');
    
    // Clear input field
    document.getElementById('messageInput').value = '';
}

// Add message to chat UI
function addMessage(content, type) {
    const chatMessages = document.querySelector('.chat-messages');
    if (!chatMessages) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', `message-${type}`);
    
    messageDiv.innerHTML = `
        <div class="message-content">${content}</div>
        <div class="message-time">${new Date().toLocaleTimeString()}</div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Show alert message
function showAlert(message, type = 'info') {
    const alertsContainer = document.querySelector('.alerts-container') || document.createElement('div');
    
    if (!document.querySelector('.alerts-container')) {
        alertsContainer.classList.add('alerts-container', 'position-fixed', 'top-0', 'end-0', 'p-3');
        document.body.appendChild(alertsContainer);
    }
    
    const alertDiv = document.createElement('div');
    alertDiv.classList.add('alert', `alert-${type}`, 'alert-dismissible', 'fade', 'show');
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    alertsContainer.appendChild(alertDiv);
    
    // Auto dismiss after 5 seconds
    setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alertDiv);
        bsAlert.close();
    }, 5000);
}

// Setup mood selection functionality
function setupMoodSelection() {
    const moodOptions = document.querySelectorAll('.mood-option');
    const moodInput = document.getElementById('moodInput');
    
    if (!moodOptions.length || !moodInput) {
        return; // Not on a mood tracking page
    }
    
    moodOptions.forEach(option => {
        option.addEventListener('click', function() {
            // Remove selected class from all options
            moodOptions.forEach(op => op.classList.remove('selected'));
            
            // Add selected class to clicked option
            this.classList.add('selected');
            
            // Update hidden input value
            moodInput.value = this.dataset.mood;
        });
    });
}

// Initialize charts for dashboard
function initCharts() {
    const moodChartCanvas = document.getElementById('moodChart');
    
    if (!moodChartCanvas) {
        return; // Not on dashboard page
    }
    
    // Get data from the canvas data attributes
    const labels = JSON.parse(moodChartCanvas.dataset.labels || '[]');
    const values = JSON.parse(moodChartCanvas.dataset.values || '[]');
    
    // Create mood trend chart
    const moodChart = new Chart(moodChartCanvas, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: '감정 상태',
                data: values,
                borderColor: '#5e72e4',
                backgroundColor: 'rgba(94, 114, 228, 0.1)',
                borderWidth: 2,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    min: -2,
                    max: 2,
                    ticks: {
                        callback: function(value) {
                            // Convert numeric values to mood labels
                            const moodLabels = {
                                '-2': '매우 나쁨',
                                '-1': '나쁨',
                                '0': '보통',
                                '1': '좋음',
                                '2': '매우 좋음'
                            };
                            return moodLabels[value] || value;
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const moodLabels = {
                                '-2': '매우 나쁨',
                                '-1': '나쁨',
                                '0': '보통',
                                '1': '좋음',
                                '2': '매우 좋음'
                            };
                            return moodLabels[context.raw] || context.raw;
                        }
                    }
                }
            }
        }
    });
    
    // Initialize other charts as needed
    initSentimentChart();
}

// Initialize sentiment analysis chart
function initSentimentChart() {
    const sentimentChartCanvas = document.getElementById('sentimentChart');
    
    if (!sentimentChartCanvas) {
        return;
    }
    
    // Get data from the canvas data attributes
    const labels = JSON.parse(sentimentChartCanvas.dataset.labels || '[]');
    const values = JSON.parse(sentimentChartCanvas.dataset.values || '[]');
    
    // Create sentiment trend chart
    const sentimentChart = new Chart(sentimentChartCanvas, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: '대화 감정 분석',
                data: values,
                borderColor: '#11cdef',
                backgroundColor: 'rgba(17, 205, 239, 0.1)',
                borderWidth: 2,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    min: -1,
                    max: 1,
                    ticks: {
                        callback: function(value) {
                            if (value === -1) return '매우 부정적';
                            if (value === -0.5) return '부정적';
                            if (value === 0) return '중립';
                            if (value === 0.5) return '긍정적';
                            if (value === 1) return '매우 긍정적';
                            return value;
                        }
                    }
                }
            }
        }
    });
}

// Handle voice profile selection
document.querySelectorAll('.voice-profile-card').forEach(card => {
    card.addEventListener('click', function() {
        // Remove selected class from all cards
        document.querySelectorAll('.voice-profile-card').forEach(c => c.classList.remove('selected'));
        
        // Add selected class to clicked card
        this.classList.add('selected');
        
        // Update hidden input value
        document.getElementById('preferredVoice').value = this.dataset.voiceId;
        
        // Play sample audio if available
        const sampleAudio = this.dataset.sampleAudio;
        if (sampleAudio) {
            const audio = new Audio(sampleAudio);
            audio.play();
        }
    });
});

// Handle sending comfort email
document.getElementById('sendComfortEmail')?.addEventListener('click', function() {
    this.disabled = true;
    this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 전송 중...';
    
    fetch('/agents/comfort-email/send/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(data.message, 'success');
        } else {
            showAlert(data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('이메일 전송 중 오류가 발생했습니다.', 'danger');
    })
    .finally(() => {
        this.disabled = false;
        this.innerHTML = '위로 이메일 보내기';
    });
});

// Message form submission
document.getElementById('messageForm')?.addEventListener('submit', function(e) {
    e.preventDefault();
    
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    
    if (message && window.conversationSocket && window.conversationSocket.readyState === WebSocket.OPEN) {
        sendTextMessage(message);
    } else if (message) {
        // Fallback to AJAX if WebSocket is not available
        submitMessageViaAjax(message);
    }
});

// Submit message via AJAX if WebSocket not available
function submitMessageViaAjax(message) {
    const conversationId = document.getElementById('conversation-id').value;
    const voiceId = document.getElementById('voiceSelect')?.value || 'default';
    
    // Display user message immediately
    addMessage(message, 'user');
    
    // Clear input field
    document.getElementById('messageInput').value = '';
    
    // Show loading indicator
    const loadingIndicator = document.createElement('div');
    loadingIndicator.classList.add('message', 'message-assistant', 'loading');
    loadingIndicator.innerHTML = `
        <div class="message-content">
            <div class="spinner-grow spinner-grow-sm text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <div class="spinner-grow spinner-grow-sm text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <div class="spinner-grow spinner-grow-sm text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `;
    
    const chatMessages = document.querySelector('.chat-messages');
    if (chatMessages) {
        chatMessages.appendChild(loadingIndicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Send request to server
    fetch(`/api/conversations/${conversationId}/send_message/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            content: message,
            voice_id: voiceId
        })
    })
    .then(response => response.json())
    .then(data => {
        // Remove loading indicator
        loadingIndicator.remove();
        
        // Display assistant response
        addMessage(data.assistant_message.content, 'assistant');
        
        // Play voice response if available
        if (data.voice_file) {
            const audio = new Audio(data.voice_file);
            audio.play();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        loadingIndicator.remove();
        showAlert('메시지 전송 중 오류가 발생했습니다.', 'danger');
    });
}
