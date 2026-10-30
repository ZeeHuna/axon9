// AXON-9 service worker v3.4.7
// 1) always loads the NEWEST app from GitHub (no old copies), 2) phone notifications open the app
self.addEventListener('install', function () { self.skipWaiting(); });
self.addEventListener('activate', function (e) { e.waitUntil(self.clients.claim()); });
self.addEventListener('fetch', function (e) {
  var u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== self.location.origin) return;
  if (e.request.mode === 'navigate' || /\.(html|js|json)$/.test(u.pathname) || u.pathname.endsWith('/')) {
    e.respondWith(fetch(e.request, { cache: 'no-store' }).catch(function () { return fetch(e.request); }));
  }
});
self.addEventListener('notificationclick', function (e) {
  e.notification.close();
  e.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (cs) {
    for (var i = 0; i < cs.length; i++) if ('focus' in cs[i]) return cs[i].focus();
    return self.clients.openWindow('./');
  }));
});
