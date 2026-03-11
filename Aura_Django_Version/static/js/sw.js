const CACHE_NAME = 'aurahealth-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/static/css/styles.css',
  '/static/js/main.js',
  '/static/js/reminders.js',
  'https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap',
  '/static/images/icon-192.png',
  '/static/images/icon-512.png'
];

// Install Event
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('Opened cache');
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
});

// Activate Event
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Fetch Event
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      // Cache hit - return response
      if (response) {
        return response;
      }

      // Clone the request
      const fetchRequest = event.request.clone();

      return fetch(fetchRequest)
        .then((response) => {
          // Check if we received a valid response
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }

          // Clone the response
          const responseToCache = response.clone();

          // Don't cache POST requests or sensitive dynamic content
          if (event.request.method === 'GET') {
              caches.open(CACHE_NAME).then((cache) => {
                cache.put(event.request, responseToCache);
              });
          }

          return response;
        })
        .catch(() => {
          // If fetch fails (offline), and it's a page navigation, return the offline fallback
          if (event.request.mode === 'navigate') {
            return caches.match('/');
          }
        });
    })
  );
});

// Push notification handling (future integration placeholder)
self.addEventListener('push', (event) => {
  const data = event.data ? event.data.json() : { title: 'Health Reminder', body: 'Time for your checkup!' };
  const options = {
    body: data.body,
    icon: '/static/images/icon-192.png',
    badge: '/static/images/icon-192.png'
  };
  event.waitUntil(self.registration.showNotification(data.title, options));
});
