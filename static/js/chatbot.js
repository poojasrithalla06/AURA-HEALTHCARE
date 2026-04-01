document.addEventListener('DOMContentLoaded', () => {
    const chatInput = document.getElementById('aiChatInput');
    const sendBtn = document.getElementById('aiSendBtn');
    const micBtn = document.getElementById('aiMicBtn');
    const chatWindow = document.getElementById('chatWindow');
    const langSelect = document.getElementById('chatLangSelect');
    const listeningIndicator = document.getElementById('listeningIndicator');
    const voiceToggleBtn = document.getElementById('voiceToggleBtn');

    if (!chatInput || !sendBtn || !chatWindow) {
        console.warn("Chatbot elements not found. Skipping chat initialization.");
        return;
    }

    // Load stored language preference
    const storedLang = localStorage.getItem('chatLanguage');
    if (storedLang && langSelect) {
        langSelect.value = storedLang;
    }
    if (langSelect) {
        langSelect.addEventListener('change', () => {
            localStorage.setItem('chatLanguage', langSelect.value);
        });
    }

    // Voice Output Setup (Text-to-Speech)
    let isVoiceEnabled = localStorage.getItem('voiceOutput') === 'true';

    const updateVoiceUI = () => {
        if (!voiceToggleBtn) return;
        const icon = voiceToggleBtn.querySelector('i');
        const text = voiceToggleBtn.querySelector('span');
        if (isVoiceEnabled) {
            icon.className = 'fas fa-volume-up';
            text.innerText = 'Voice On';
            voiceToggleBtn.style.background = 'var(--primary-color)';
            voiceToggleBtn.style.color = 'white';
        } else {
            icon.className = 'fas fa-volume-mute';
            text.innerText = 'Voice Off';
            voiceToggleBtn.style.background = 'var(--secondary-color)';
            voiceToggleBtn.style.color = 'var(--text-main)';
        }
    };

    updateVoiceUI();

    const speakResponse = (text) => {
        if (!isVoiceEnabled || !('speechSynthesis' in window)) return;
        const cleanText = text.replace(/\*\*/g, '');
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(cleanText);
        const langMap = { 'English': 'en-US', 'Hindi': 'hi-IN', 'Telugu': 'te-IN' };
        const currentLang = langSelect ? langSelect.value : 'English';
        utterance.lang = langMap[currentLang] || 'en-US';
        
        const voices = window.speechSynthesis.getVoices();
        if (voices.length > 0) {
            let preferredVoice = voices.find(v => v.lang.replace('_', '-').toLowerCase().includes(utterance.lang.toLowerCase()));
            if (!preferredVoice) {
                preferredVoice = voices.find(v => v.lang.toLowerCase().startsWith(utterance.lang.split('-')[0].toLowerCase()));
            }
            if (preferredVoice) utterance.voice = preferredVoice;
        }
        
        window.speechSynthesis.speak(utterance);
    };

    // Speak initial message if voice is already ON
    if (isVoiceEnabled) {
        speakResponse("Hello! I am Aura. How can I assist you with your health today?");
    }

    if (voiceToggleBtn) {
        voiceToggleBtn.addEventListener('click', () => {
            isVoiceEnabled = !isVoiceEnabled;
            localStorage.setItem('voiceOutput', isVoiceEnabled);
            updateVoiceUI();
            if (!isVoiceEnabled && window.speechSynthesis.speaking) {
                window.speechSynthesis.cancel();
            } else if (isVoiceEnabled) {
                // Direct user interaction forces the browser to allow speech synthesis
                const utterance = new SpeechSynthesisUtterance("Voice is now enabled");
                window.speechSynthesis.speak(utterance);
            }
        });
    }

    // Web Speech API Setup (Native Browser Transcription)
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition;
    let isListening = false;

    if (SpeechRecognition && micBtn) {
        console.log("Speech Recognition supported and button found.");
        const setupRecognition = () => {
            recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;

            recognition.onstart = () => {
                console.log("Speech Recognition session started successfully.");
                isListening = true;
                micBtn.style.background = '#ef4444';
                micBtn.style.color = 'white';
                micBtn.innerHTML = '<i class="fas fa-stop"></i>';
                if (listeningIndicator) listeningIndicator.style.display = 'flex';
                chatInput.placeholder = "Listening... Speak now.";
            };

            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                console.log("Transcribed text:", transcript);
                chatInput.value = transcript;
                if (chatInput.value.trim() !== "") {
                    runChatSequence();
                }
            };

            recognition.onerror = (event) => {
                console.error('Speech Recognition Error:', event.error, event.message);
                stopListeningUI();
                
                if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
                    alert('CRITICAL: Microphone access is BLOCKED by your browser.\n\n1. Click the LOCK (🔒) or SLIDER icon in the URL bar (next to 127.0.0.1).\n2. Toggle "Microphone" to ON.\n3. Reload the page.\n\nAlternatively, ensure you are using Chrome or Edge.');
                } else if (event.error === 'no-speech') {
                    console.warn("No speech was detected.");
                } else if (event.error === 'network') {
                    alert('Network error during speech recognition. Ensure you are online.');
                }
            };

            recognition.onend = () => {
                console.log("Speech Recognition session ended.");
                stopListeningUI();
            };
        };

        const stopListeningUI = () => {
            isListening = false;
            micBtn.style.background = '#f1f5f9';
            micBtn.style.color = 'var(--primary-color)';
            micBtn.innerHTML = '<i class="fas fa-microphone"></i>';
            if (listeningIndicator) listeningIndicator.style.display = 'none';
            chatInput.placeholder = "Type your message...";
        };

        setupRecognition();

        micBtn.addEventListener('click', async (e) => {
            console.log("Mic Button Clicked. Current State: " + (isListening ? "Listening" : "Idle"));
            
            if (isListening) {
                try { recognition.stop(); } catch(e) {}
                stopListeningUI();
                return;
            }

            // Check if user has granted mic permission first
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                stream.getTracks().forEach(track => track.stop()); // Just checking, don't keep it open
                
                const bcp47Map = { 'English': 'en-US', 'Hindi': 'hi-IN', 'Telugu': 'te-IN' };
                const currentLang = langSelect ? langSelect.value : 'English';
                recognition.lang = bcp47Map[currentLang] || 'en-US';
                
                console.log("Requesting Speech Recognition Start for language: " + recognition.lang);
                recognition.start();
            } catch (err) {
                console.error("Mic Permission or Start Error:", err);
                if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
                    alert("MICROPHONE BLOCKED: Please enable mic permission in your browser settings (click the icon at the far left of the address bar).");
                } else {
                    alert("Could not start microphone. Error: " + err.message);
                }
                stopListeningUI();
            }
        });
    } else {
        console.warn("Speech Recognition NOT supported or button NOT found.");
        if (micBtn) micBtn.style.opacity = '0.5';
    }

    const appendMessage = (text, sender) => {
        const formattedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        const formattedLines = formattedText.replace(/\n/g, '<br>');
        const div = document.createElement('div');
        div.className = sender === 'user' ? 'user-msg-dynamic' : 'bot-msg-dynamic';
        
        if (sender === 'bot') {
            div.innerHTML = `
                <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.3rem;">
                    <i class="fas fa-robot" style="color: var(--primary-color);"></i>
                    <strong style="font-size: 0.85rem; color: var(--primary-color);">Aura AI</strong>
                </div>
                <span>${formattedLines}</span>
            `;
        } else {
            div.innerText = text;
        }

        chatWindow.appendChild(div);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    };

    const runChatSequence = async () => {
        const msg = chatInput.value.trim();
        if (!msg) return;

        appendMessage(msg, 'user');
        chatInput.value = '';

        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'bot-msg-dynamic';
        typingIndicator.id = 'tempTypingIndicator';
        typingIndicator.innerHTML = `
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.3rem;">
                <i class="fas fa-robot" style="color: var(--primary-color);"></i>
                <strong style="font-size: 0.85rem; color: var(--primary-color);">Aura AI</strong>
            </div>
            <div class="typing-dots"><span></span><span></span><span></span></div>
        `;
        chatWindow.appendChild(typingIndicator);
        chatWindow.scrollTop = chatWindow.scrollHeight;

        try {
            const currentLang = langSelect ? langSelect.value : 'English';
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: msg, language: currentLang })
            });
            const data = await response.json();
            
            const typingEl = document.getElementById('tempTypingIndicator');
            if(typingEl) typingEl.remove();
            
            if (data.response) {
                appendMessage(data.response, 'bot');
                speakResponse(data.response);
            } else {
                appendMessage("I couldn't process that request right now.", 'bot');
            }
        } catch (error) {
            const typingEl = document.getElementById('tempTypingIndicator');
            if(typingEl) typingEl.remove();
            appendMessage("Connection error while reaching the server.", 'bot');
        }
    };

    sendBtn.addEventListener('click', runChatSequence);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            runChatSequence();
        }
    });
});

// Feedback functions made global
let currentHelpfulStatus = true;
function openFeedback(isHelpful) {
    currentHelpfulStatus = isHelpful;
    const modal = document.getElementById('feedbackModal');
    if (modal) {
        modal.style.display = 'block';
        document.getElementById('feedbackTitle').innerText = isHelpful ? 'Glad to hear! Any additional notes?' : 'Sorry about that. How can we do better?';
    }
}

function closeFeedback() {
    const modal = document.getElementById('feedbackModal');
    if (modal) modal.style.display = 'none';
}

function submitFeedback() {
    const commentInput = document.getElementById('feedbackComment');
    const comment = commentInput ? commentInput.value : '';
    const userId = typeof USER_ID !== 'undefined' ? USER_ID : null;

    fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: userId,
            comment: comment,
            helpful: currentHelpfulStatus
        })
    })
    .then(res => res.json())
    .then(data => {
        alert("Thank you for your feedback!");
        closeFeedback();
        if (commentInput) commentInput.value = '';
    });
}
