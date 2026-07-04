/* Home Strength Blueprint — service worker (registered over https only).
   HTML is network-first so deployed updates reach installed users
   immediately; static assets are cache-first for speed. Everything still
   works fully offline via the cache fallback. */
const CACHE = "hsb-v2";
const ASSETS = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./icon-192.png",
  "./icon-512.png",
  "./apple-touch-icon.png"
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  const isHTML = req.mode === "navigate" || url.pathname.endsWith("/index.html");
  if (isHTML) {
    // network-first: fresh deploys win, cache covers offline
    e.respondWith(
      fetch(req)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put("./index.html", copy));
          return res;
        })
        .catch(() =>
          caches.match(req, { ignoreSearch: true }).then((h) => h || caches.match("./index.html"))
        )
    );
    return;
  }

  // cache-first for icons/manifest, refreshed in the background
  e.respondWith(
    caches.match(req, { ignoreSearch: true }).then((hit) => {
      const refetch = fetch(req)
        .then((res) => {
          if (res && res.ok) {
            const copy = res.clone();
            caches.open(CACHE).then((c) => c.put(req, copy));
          }
          return res;
        })
        .catch(() => hit);
      return hit || refetch;
    })
  );
});
