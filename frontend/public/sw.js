// OneGoal Pro — Service Worker
// Handles: offline fallback for page navigations, push notifications, notification clicks.
// Bump CACHE_VERSION whenever offline.html changes, so users get the new copy.

const CACHE_VERSION = 'onegoal-offline-v1';
const OFFLINE_URL = '/offline.html';

// Install: cache the offline page so it is available with no connection.
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_VERSION).then(function(cache) {
      return cache.add(new Request(OFFLINE_URL, { cache: 'reload' }));
    })
  );
  self.skipWaiting();
});

// Activate: remove old offline caches and take control of open pages.
self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(keys) {
      return Promise.all(
        keys
          .filter(function(key) { return key.startsWith('onegoal-offline-') && key !== CACHE_VERSION; })
          .map(function(key) { return caches.delete(key); })
      );
    }).then(function() {
      return self.clients.claim();
    })
  );
});

// Fetch: only page navigations are handled. API calls, images, scripts and
// everything else go straight to the network exactly as before.
self.addEventListener('fetch', function(event) {
  if (event.request.mode !== 'navigate') return;

  event.respondWith(
    fetch(event.request).catch(function() {
      return caches.match(OFFLINE_URL);
    })
  );
});

// Push: show the notification.
self.addEventListener('push', function(event) {
  if (!event.data) return;

  let data;
  try {
    data = event.data.json();
  } catch {
    data = { title: 'OneGoal Pro', body: event.data.text() };
  }

  const title = data.title || 'OneGoal Pro';
  const options = {
    body: data.body || 'Your identity task for today is ready.',
    icon: '/icon-192.png',
    badge: '/icon-72.png',
    tag: 'onegoal-daily-task',
    renotify: true,
    data: {
      url: data.url || '/dashboard',
    },
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// Notification click: open the target page. If the app is already open,
// bring it forward AND move it to the target page (previously it only focused).
self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  const path = event.notification.data?.url || '/dashboard';
  const target = 'https://onegoalpro.app' + path;

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function(clientList) {
      for (const client of clientList) {
        if (client.url.includes('onegoalpro.app') && 'focus' in client) {
          return client.focus().then(function(focused) {
            if (focused && 'navigate' in focused && focused.url !== target) {
              // navigate() can fail on pages this worker does not control yet;
              // fall back to opening a new window in that case.
              return focused.navigate(target).catch(function() {
                return clients.openWindow(target);
              });
            }
            return focused;
          });
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(target);
      }
    })
  );
});
