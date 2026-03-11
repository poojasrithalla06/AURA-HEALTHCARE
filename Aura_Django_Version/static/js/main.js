// Service Worker Registration
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/js/sw.js')
            .then(registration => {
                console.log('SW registered: ', registration);
            })
            .catch(registrationError => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}

// Offline Mode Indicator
window.addEventListener('online', updateOnlineStatus);
window.addEventListener('offline', updateOnlineStatus);

function updateOnlineStatus() {
    const status = navigator.onLine ? 'online' : 'offline';
    console.log('User is now', status);
    
    // Create status indicator if it doesn't exist
    let indicator = document.getElementById('offline-indicator');
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.id = 'offline-indicator';
        indicator.style.cssText = `
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            padding: 12px 24px;
            background: rgba(239, 68, 68, 0.9);
            backdrop-filter: blur(10px);
            color: white;
            border-radius: 12px;
            font-weight: 700;
            font-family: 'Outfit', sans-serif;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            z-index: 9999;
            display: none;
            align-items: center;
            gap: 12px;
            border: 1px solid rgba(255,255,255,0.2);
        `;
        indicator.innerHTML = `<span style="font-size: 1.2rem;">📡</span> <span>Neural link offline. Data cached for local sync.</span>`;
        document.body.appendChild(indicator);
    }

    if (status === 'offline') {
        indicator.style.display = 'flex';
    } else {
        indicator.style.display = 'none';
        // Potential sync logic here
        syncOfflineData();
    }
}

// IndexedDB Initialization for Offline Data
const dbName = "AuraHealthDB";
const dbVersion = 1;
let db;

const request = indexedDB.open(dbName, dbVersion);

request.onerror = (event) => {
    console.error("Database error: " + event.target.errorCode);
};

request.onsuccess = (event) => {
    db = event.target.result;
    console.log("IndexedDB initialized");
};

request.onupgradeneeded = (event) => {
    const db = event.target.result;
    if (!db.objectStoreNames.contains("pendingTasks")) {
        db.createObjectStore("pendingTasks", { keyPath: "id", autoIncrement: true });
    }
    if (!db.objectStoreNames.contains("pendingMetrics")) {
        db.createObjectStore("pendingMetrics", { keyPath: "id", autoIncrement: true });
    }
};

// Function to store pending tasks when offline
function savePendingTask(taskData) {
    if (!db) return;
    const transaction = db.transaction(["pendingTasks"], "readwrite");
    const objectStore = transaction.objectStore("pendingTasks");
    objectStore.add(taskData);
}

// Function to store pending metrics when offline
function savePendingMetric(metricData) {
    if (!db) return;
    const transaction = db.transaction(["pendingMetrics"], "readwrite");
    const objectStore = transaction.objectStore("pendingMetrics");
    objectStore.add(metricData);
}

// Function to sync data when back online
function syncOfflineData() {
    if (!db) return;
    
    // Sync Tasks
    const taskTx = db.transaction(["pendingTasks"], "readwrite");
    const taskStore = taskTx.objectStore("pendingTasks");
    const taskRequest = taskStore.getAll();

    taskRequest.onsuccess = () => {
        taskRequest.result.forEach(task => {
            fetch('/create-task/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: new URLSearchParams(task)
            })
            .then(res => {
                if (res.ok) {
                    const delTx = db.transaction(["pendingTasks"], "readwrite");
                    delTx.objectStore("pendingTasks").delete(task.id);
                }
            });
        });
    };

    // Sync Metrics
    const metricTx = db.transaction(["pendingMetrics"], "readwrite");
    const metricStore = metricTx.objectStore("pendingMetrics");
    const metricRequest = metricStore.getAll();

    metricRequest.onsuccess = () => {
        metricRequest.result.forEach(metric => {
            fetch('/health-metrics/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: new URLSearchParams(metric)
            })
            .then(res => {
                if (res.ok) {
                    const delTx = db.transaction(["pendingMetrics"], "readwrite");
                    delTx.objectStore("pendingMetrics").delete(metric.id);
                }
            });
        });
    };
}

// Helper to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Check status on load
document.addEventListener('DOMContentLoaded', () => {
    updateOnlineStatus();
    
    // Intercept form submissions for offline support
    const taskForm = document.querySelector('#task-form');
    if (taskForm) {
        taskForm.addEventListener('submit', (e) => {
            if (!navigator.onLine) {
                e.preventDefault();
                const formData = new FormData(taskForm);
                const taskData = {};
                formData.forEach((value, key) => { taskData[key] = value; });
                savePendingTask(taskData);
                alert("Task saved locally. It will sync when Aura neural link is restored.");
                window.location.href = '/dashboard/';
            }
        });
    }

    const healthForm = document.querySelector('form[action*="health-metrics"], form:has(select[name="metric_type"])');
    if (healthForm) {
        healthForm.addEventListener('submit', (e) => {
            if (!navigator.onLine) {
                e.preventDefault();
                const formData = new FormData(healthForm);
                const metricData = {};
                formData.forEach((value, key) => { metricData[key] = value; });
                savePendingMetric(metricData);
                alert("Biometrics saved locally. Syncing once online.");
                window.location.href = '/health-metrics/';
            }
        });
    }
});
