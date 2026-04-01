document.addEventListener('DOMContentLoaded', function () {

    // Voice Recognition Setup
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition;
    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.lang = 'en-US';
        recognition.continuous = false;

        const micBtn = document.getElementById('micBtn');
        if (micBtn) {
            micBtn.addEventListener('click', () => {
                const langSelect = document.getElementById('languageSelect');
                const currentLang = langSelect ? langSelect.value : 'English';
                const bcp47Map = { 'English': 'en-US', 'Hindi': 'hi-IN', 'Telugu': 'te-IN' };
                recognition.lang = bcp47Map[currentLang] || 'en-US';
                recognition.start();
            });

            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                const chatInput = document.getElementById('chatInput');
                if (chatInput) {
                    chatInput.value = transcript;
                    sendMessage();
                }
            };
        }
    }

    // Chart.js Init (Dashboard)
    const ctx = document.getElementById('healthTrendChart');
    if (ctx) {
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Heart Rate (bpm)',
                    data: [72, 75, 70, 68, 74, 71, 73],
                    borderColor: '#3b82f6',
                    borderWidth: 3,
                    pointRadius: 3,
                    tension: 0.4,
                    fill: false
                }, {
                    label: 'SpO2 (%)',
                    data: [98, 97, 99, 98, 97, 98, 99],
                    borderColor: '#14b8a6',
                    borderWidth: 3,
                    pointRadius: 3,
                    tension: 0.4,
                    fill: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: { color: '#f1f5f9' },
                        ticks: { color: '#94a3b8' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#94a3b8' }
                    }
                }
            }
        });

        // Mock Risk Calculation for UI
        fetch('/api/predict_risk', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ heart_rate: 72, risk_factors: [] })
        })
            .then(res => res.json())
            .then(data => {
                const riskBar = document.getElementById('riskBar');
                const riskText = document.getElementById('riskText');
                if (riskBar) {
                    riskBar.style.width = data.risk_score + '%';
                    // Color based on risk
                    if (data.risk_score > 60) riskBar.style.background = '#F44336';
                    else if (data.risk_score > 30) riskBar.style.background = '#FF9800';
                    else riskBar.style.background = '#4CAF50';

                    riskText.innerText = data.risk_score + '% Risk (' + data.category + ')';
                }
            });
    }

    loadMedications();

});

function changeLanguage() {
    const lang = document.getElementById('languageSelect').value;
    console.log("Language switched to: " + lang);
}

function sendMessage() {
    const input = document.getElementById('chatInput');
    const msg = input.value;
    if (!msg) return;

    addMessage(msg, 'user-msg');
    input.value = '';

    // Simulate AI thinking logic
    const chatWindow = document.getElementById('chatWindow');
    const typingIndicator = document.createElement('div');
    typingIndicator.className = 'chat-bubble bot-msg';
    typingIndicator.id = 'typingIndicator';
    typingIndicator.innerText = '...';
    chatWindow.appendChild(typingIndicator);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    setTimeout(() => {
        fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: msg,
                language: document.getElementById('languageSelect')?.value || 'English'
            })
        })
            .then(res => res.json())
            .then(data => {
                const typing = document.getElementById('typingIndicator');
                if (typing) typing.remove();

                addMessage(data.response, 'bot-msg');
                speak(data.response);
            })
            .catch(err => {
                const typing = document.getElementById('typingIndicator');
                if (typing) typing.remove();
                addMessage("I'm sorry, I could not connect to the local AI. Please check if Ollama is running.", 'bot-msg');
            });
    }, 1000);
}

function addMessage(text, className) {
    const chatWindow = document.getElementById('chatWindow');
    const div = document.createElement('div');
    div.className = 'chat-bubble ' + className;
    div.innerText = text;
    chatWindow.appendChild(div);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function speak(text) {
    if (!window.speechSynthesis) return;
    const utterance = new SpeechSynthesisUtterance(text);
    const langSelect = document.getElementById('languageSelect');
    const currentLang = langSelect ? langSelect.value : 'English';
    const bcp47Map = { 'English': 'en-IN', 'Hindi': 'hi-IN', 'Telugu': 'te-IN' };
    utterance.lang = bcp47Map[currentLang] || 'en-IN';
    window.speechSynthesis.speak(utterance);
}

function triggerSOS() {
    if (confirm("Are you sure you want to trigger the EMERGENCY SOS?")) {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition((position) => {
                sendSOS(position.coords.latitude + ", " + position.coords.longitude);
            }, () => {
                sendSOS("Unknown Location (GPS Denied)");
            });
        } else {
            sendSOS("Unknown Location (No GPS)");
        }
    }
}

function sendSOS(loc) {
    const finalUserId = USER_ID && USER_ID !== 'None' ? USER_ID : 1;
    fetch('/api/sos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: finalUserId,
            location: loc
        })
    })
        .then(res => res.json())
        .then(data => alert(data.message))
        .catch(err => alert("SOS Failed: Local network error. Please try again."));
}

let loadedMeds = [];

function loadMedications() {
    if (typeof USER_ID === 'undefined') return;

    // Request Notification permission
    if ("Notification" in window && Notification.permission === "default") {
        Notification.requestPermission();
    }

    fetch('/api/medication?user_id=' + USER_ID)
        .then(res => res.json())
        .then(data => {
            loadedMeds = data;
            const list = document.getElementById('medList');
            if (!list) return;
            list.innerHTML = '';
            if (data.length === 0) list.innerHTML = '<li style="color:#999; padding: 10px;">No reminders set.</li>';

            data.forEach(med => {
                const li = document.createElement('li');
                li.style.cssText = "padding: 0.8rem; border-bottom: 1px solid #f0f0f0; display: flex; justify-content: space-between; align-items: center;";
                li.innerHTML = `
                <div style="display:flex; align-items:center;">
                    <i class="fas fa-capsules" style="color: var(--primary); margin-right: 10px;"></i>
                    <div>
                        <span style="display:block; font-weight: 500;">${med.name || med.medicine_name}</span>
                        <small style="color:#999;">${med.frequency || med.status || 'Daily'}</small>
                    </div>
                </div>
                <span style="font-weight: bold; color: var(--accent); background: #ffebee; padding: 2px 8px; border-radius: 10px; font-size: 0.8rem;">${med.time}</span>
            `;
                list.appendChild(li);
            });
        });
}

// Check for medication reminders every minute
setInterval(() => {
    const now = new Date();
    const currentTime = now.getHours().toString().padStart(2, '0') + ":" + now.getMinutes().toString().padStart(2, '0');

    loadedMeds.forEach(med => {
        // Handle both 24h and 12h formats if necessary, assuming 24h from input
        if (med.time === currentTime) {
            triggerMedicationAlert(med);
        }
    });
}, 60000);

function triggerMedicationAlert(med) {
    const title = "💊 Medication Reminder: " + med.name;
    const options = {
        body: "It's time to take your " + med.name + ". Stay healthy!"
    };

    if ("Notification" in window && Notification.permission === "granted") {
        new Notification(title, options);
    } else {
        alert(title + "\n" + options.body);
    }
}

function addMedication() {
    window.location.href = "/medication";
}
