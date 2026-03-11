document.addEventListener('DOMContentLoaded', () => {
    // -----------------------------------------------------
    // 1. Online Alarm Sounds from Freesound
    // -----------------------------------------------------
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    let isNotificationsEnabled = false;
    let currentAudio = null;

    // Online alarm sounds - free from Freesound & other sources
    const alarmSounds = {
        classic: 'https://cdn.freesound.org/previews/520/520654_9497059-lq.mp3',
        digital: 'https://cdn.freesound.org/previews/255/255018_4182424-lq.mp3',
        bell: 'https://cdn.freesound.org/previews/323/323951_5228024-lq.mp3',
        siren: 'https://cdn.freesound.org/previews/442/442605_7037018-lq.mp3',
        chime: 'https://cdn.freesound.org/previews/388/388106_6652508-lq.mp3',
        beep: 'https://cdn.freesound.org/previews/597/597788_10438393-lq.mp3',
        warning: 'https://cdn.freesound.org/previews/219/219244_4057602-lq.mp3',
        nature: 'https://cdn.freesound.org/previews/413/413749_7668612-lq.mp3'
    };

    // Fallback synthesized sounds
    const syntheticSounds = {
        beep: () => {
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.connect(gain);
            gain.connect(audioCtx.destination);

            osc.type = 'sine';
            osc.frequency.setValueAtTime(440, audioCtx.currentTime);
            osc.frequency.exponentialRampToValueAtTime(880, audioCtx.currentTime + 0.1);

            gain.gain.setValueAtTime(0.5, audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.5);

            osc.start();
            osc.stop(audioCtx.currentTime + 0.5);
        },
        chime: () => {
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.connect(gain);
            gain.connect(audioCtx.destination);

            osc.type = 'triangle';
            osc.frequency.setValueAtTime(523.25, audioCtx.currentTime); // C5

            gain.gain.setValueAtTime(0, audioCtx.currentTime);
            gain.gain.linearRampToValueAtTime(0.3, audioCtx.currentTime + 0.1);
            gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 2);

            osc.start();
            osc.stop(audioCtx.currentTime + 2);
        },
        digital: () => {
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.connect(gain);
            gain.connect(audioCtx.destination);

            osc.type = 'square';
            osc.frequency.setValueAtTime(800, audioCtx.currentTime);
            osc.frequency.setValueAtTime(0, audioCtx.currentTime + 0.1);
            osc.frequency.setValueAtTime(800, audioCtx.currentTime + 0.2);

            gain.gain.value = 0.1;

            osc.start();
            osc.stop(audioCtx.currentTime + 0.3);
        },
        siren: () => {
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.connect(gain);
            gain.connect(audioCtx.destination);

            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(600, audioCtx.currentTime);
            osc.frequency.linearRampToValueAtTime(1200, audioCtx.currentTime + 0.5);
            osc.frequency.linearRampToValueAtTime(600, audioCtx.currentTime + 1.0);

            gain.gain.value = 0.2;

            osc.start();
            osc.stop(audioCtx.currentTime + 1.0);
        }
    };

    function playSound(type) {
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }

        // Stop any currently playing audio
        if (currentAudio) {
            currentAudio.pause();
            currentAudio.currentTime = 0;
        }

        // Try online sound first
        if (alarmSounds[type]) {
            const audio = new Audio(alarmSounds[type]);
            audio.volume = 0.7;
            audio.play().catch(() => {
                // Fallback to synthetic sound if online sound fails
                const synthFunc = syntheticSounds[type] || syntheticSounds['beep'];
                synthFunc();
            });
            currentAudio = audio;
        } else {
            // Use synthetic sound
            const synthFunc = syntheticSounds[type] || syntheticSounds['beep'];
            synthFunc();
        }
    }

    // -----------------------------------------------------
    // 2. Settings Modal Logic
    // -----------------------------------------------------
    const settingsBtn = document.getElementById('settingsBtn');
    const settingsModal = document.getElementById('settingsModal');
    const closeSettingsBtn = document.getElementById('closeSettingsBtn');
    const testSoundBtn = document.getElementById('testSoundBtn');
    const alarmSoundSelect = document.getElementById('alarmSound');
    const enableNotifBtn = document.getElementById('enableNotifBtn');

    // Track triggered alarms to avoid spamming
    const triggeredAlarms = new Set();

    if (settingsBtn) {
        settingsBtn.addEventListener('click', () => {
            settingsModal.style.display = 'flex';
        });
    }

    if (closeSettingsBtn) {
        closeSettingsBtn.addEventListener('click', () => {
            settingsModal.style.display = 'none';
        });
    }

    if (settingsModal) {
        settingsModal.addEventListener('click', (e) => {
            if (e.target === settingsModal) {
                settingsModal.style.display = 'none';
            }
        });
    }

    if (testSoundBtn && alarmSoundSelect) {
        testSoundBtn.addEventListener('click', () => {
            const selectedSound = alarmSoundSelect.value;
            playSound(selectedSound);
        });
    }

    if (enableNotifBtn) {
        enableNotifBtn.addEventListener('click', () => {
            if (!("Notification" in window)) {
                alert("This browser does not support desktop notification");
            } else if (Notification.permission === "granted") {
                new Notification("Notifications already enabled!");
                isNotificationsEnabled = true;
            } else if (Notification.permission !== "denied") {
                Notification.requestPermission().then(function (permission) {
                    if (permission === "granted") {
                        new Notification("Notifications enabled!");
                        isNotificationsEnabled = true;
                    }
                });
            }
        });
    }

    // Check permission on load
    if (Notification.permission === "granted") {
        isNotificationsEnabled = true;
    }

    // -----------------------------------------------------
    // 3. Countdown & Alarm Logic
    // -----------------------------------------------------
    function updateCountdowns() {
        const now = new Date();
        const tasks = document.querySelectorAll('.task-card');

        tasks.forEach(task => {
            const dueDateStr = task.getAttribute('data-due-date');
            if (!dueDateStr) return;

            const dueDate = new Date(dueDateStr);
            const diff = dueDate - now;
            const timerSpan = task.querySelector('.countdown-timer');

            // Find Task ID
            const editLink = task.querySelector('a[href*="update_task"]');
            if (!editLink) return;
            // Assumes URL structure like /update-task/1/
            const taskId = editLink.getAttribute('href').split('/').filter(Boolean).pop();

            if (!timerSpan) return;

            if (diff <= 0) {
                timerSpan.textContent = "Overdue";
                timerSpan.style.background = "#fee2e2"; // Red bg
                timerSpan.style.color = "#b91c1c";

                // Trigger Alarm if it became overdue recently (within last 2s)
                if (Math.abs(diff) < 2000 && !triggeredAlarms.has(taskId)) {
                    // Check if notifications enabled (or just play sound if user interacted)
                    playSound(alarmSoundSelect ? alarmSoundSelect.value : 'beep');

                    if (isNotificationsEnabled) {
                        new Notification("Task Overdue!", {
                            body: task.querySelector('h3').innerText.trim(),
                        });
                    }
                    triggeredAlarms.add(taskId);
                }
            } else {
                const days = Math.floor(diff / (1000 * 60 * 60 * 24));
                const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                const seconds = Math.floor((diff % (1000 * 60)) / 1000);

                let text = "";
                if (days > 0) text += `${days}d `;
                if (hours > 0) text += `${hours}h `;
                if (minutes > 0) text += `${minutes}m `;
                text += `${seconds}s`; // Always show seconds

                timerSpan.textContent = text;
                timerSpan.style.background = "#fff7ed";
                timerSpan.style.color = "var(--accent-color)";
            }
        });

        // -----------------------------------------------------
        // 4. Focus Mode Circular Timer Logic
        // -----------------------------------------------------
        const focusTimer = document.getElementById('focusTimer');
        const focusTimerText = document.getElementById('focusTimerText');

        if (focusTimer && focusTimerText) {
            const dueDateStr = focusTimer.getAttribute('data-due-date');
            if (dueDateStr) {
                const dueDate = new Date(dueDateStr);
                const diff = dueDate - now;

                if (diff <= 0) {
                    focusTimerText.textContent = "Overdue";
                    focusTimerText.style.color = "#ef4444";
                    const circle = document.querySelector('.progress-circle');
                    if (circle) {
                        circle.style.stroke = "#ef4444";
                        circle.style.strokeDashoffset = 0;
                    }
                } else {
                    const hours = Math.floor(diff / (1000 * 60 * 60));
                    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                    const seconds = Math.floor((diff % (1000 * 60)) / 1000);

                    // Format as HH:MM:SS
                    const formatted =
                        (hours > 0 ? String(hours).padStart(2, '0') + ':' : '') +
                        String(minutes).padStart(2, '0') + ':' +
                        String(seconds).padStart(2, '0');

                    focusTimerText.textContent = formatted;

                    // Animations: Seconds ticker (full circle = 60s)
                    const circle = document.querySelector('.progress-circle');
                    if (circle) {
                        // Circumference is approx 440 (2 * pi * 70)
                        const circumference = 440;
                        const offset = circumference - ((seconds / 60) * circumference);
                        circle.style.strokeDashoffset = offset;
                    }
                }
            }
        }
    }

    // Run every second
    setInterval(updateCountdowns, 1000);
    // Initial run
    updateCountdowns();
});
