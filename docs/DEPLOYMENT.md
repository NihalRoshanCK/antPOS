# antPOS deployment notes

## PWA (installable app)

antPOS installs as an app from the browser: Chrome/Edge show an install button
in the address bar, Android offers "Install app", and on iOS use Share → Add to
Home Screen. The installed app opens at `/antPOS` in its own window. Installing
requires HTTPS (or `localhost`).

No web server configuration is needed. The build writes the service worker to
`/assets/ant_pos/antPOS/sw.js`, but a worker only controls pages below its own
directory, so Frappe also serves that file at `/antPOS/sw.js` with a
`Service-Worker-Allowed: /antPOS` header (`ant_pos/pwa.py`, wired up through
`website_route_rules` and `page_renderer` in `hooks.py`). An nginx
`location = /assets/ant_pos/antPOS/sw.js` block from older notes is no longer
used and can be removed.

What the worker does:

- Precaches the built JS/CSS so the app loads fast and survives a restart.
- Always fetches the `/antPOS` page from the server. The built `index.html` is an
  unrendered Jinja template, so it is never served from cache. The last page the
  server returned is kept only so the installed app still opens when the
  network is down.
- Never caches `/api/` calls. Selling needs the server; there is no offline
  sales queue.
- Updates itself: after a new build, the next load picks up the new worker.

### Verifying

1. Load `/antPOS`, open DevTools → Application → Service Workers. The worker
   should be `/antPOS/sw.js`, scope `/antPOS`, "activated and is running".
2. Application → Manifest should show no errors and offer "Install".
3. `curl -I https://<site>/antPOS/sw.js` should return
   `Content-Type: application/javascript` and `Service-Worker-Allowed: /antPOS`.

## Assets

- `bench build --app ant_pos` regenerates everything under
  `ant_pos/public/antPOS/`.
- Sourcemaps are disabled (`buildConfig.sourcemap: false`). Do not re-enable for
  production builds: that directory is served publicly.
- PWA icons live in `ant_pos/public/manifest/` and are served from
  `/assets/ant_pos/manifest/`.

## Database indexes

`ant_pos.patches.v0_1_0.add_shift_lookup_indexes` adds indexes on
`Sales Invoice.custom_ant_opening` and `Payment Entry.reference_no`. Both are the
sole predicates of the shift-close and payments queries. On a large site the
patch may take a few minutes; run `bench --site <site> migrate` during a quiet
window.

## Upgrading to 0.2.0

Run `bench --site <site> migrate`. It applies
`ant_pos.patches.v0_1_0.restore_standard_permissions`, which repairs sites
installed with 0.1.0: that installer added the POS roles' permissions in a way
that made Frappe ignore every other role's permissions on the same doctypes
(Sales Invoice, Customer, Item and more). The patch restores those, leaves
doctypes an administrator has customised alone, and re-applies the POS roles'
permissions, now read-only on masters.

After upgrading, check that every cashier is listed in *Applicable for Users*
on their POS Profile: shifts can only be opened on such a profile (System
Managers excepted).
