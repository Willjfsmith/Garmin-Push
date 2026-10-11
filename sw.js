/* Home Strength Blueprint — service worker (registered over https only).
   The app page is network-first, so a new deploy reaches installed users on
   the next open; the cached copy is only used offline. Icons and the
   manifest are cache-first. Bump CACHE whenever this file's logic changes. */
const CACHE = "hsb-v3";
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
    caches.open(CACHE)
      .then((c) => c.addAll(ASSETS.map((u) => new Request(u, { cache: "reload" }))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil((async () => {
    const keys = await caches.keys();
    const stale = keys.filter((k) => k !== CACHE);
    await Promise.all(stale.map((k) => caches.delete(k)));
    await self.clients.claim();
    // replacing an older worker: reload open windows so they drop the stale page
    if (stale.length) {
      const wins = await self.clients.matchAll({ type: "window" });
      wins.forEach((w) => { try { w.navigate(w.url); } catch (_) {} });
    }
  })());
});

function isPage(req) {
  if (req.mode === "navigate") return true;
  const u = new URL(req.url);
  return u.origin === self.location.origin && (u.pathname.endsWith("/") || u.pathname.endsWith(".html"));
}

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;

  if (isPage(req)) {
    // network first; keep the cached copy fresh for offline use
    e.respondWith(
      fetch(req, { cache: "no-store" })
        .then((res) => {
          if (res && res.ok) {
            const copy = res.clone();
            caches.open(CACHE).then((c) => c.put("./index.html", copy));
          }
          return res;
        })
        .catch(() => caches.match("./index.html").then((hit) => hit || caches.match("./")))
    );
    return;
  }

  e.respondWith(
    caches.match(req, { ignoreSearch: true }).then((hit) => {
      if (hit) return hit;
      return fetch(req).then((res) => {
        if (res && res.ok && new URL(req.url).origin === self.location.origin) {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy));
        }
        return res;
      });
    })
  );
});
