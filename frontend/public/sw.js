// OneGoal Pro — Service Worker
// Handles incoming push notifications and displays them

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

self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  const url = event.notification.data?.url || '/dashboard';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function(clientList) {
      for (const client of clientList) {
        if (client.url.includes('onegoalpro.app') && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow('https://onegoalpro.app' + url);
      }
    })
  );
});
