# antPOS deployment notes

## Service worker scope (required for offline / installable PWA)

The app is routed at `/antPOS`, but its service worker is a build artifact served
from `/assets/ant_pos/antPOS/sw.js`. A service worker may only control pages at
or below its own directory, so by default this worker's scope is
`/assets/ant_pos/antPOS/` and **it never controls the app**. That is why offline
mode has never worked.

`vite.config.mjs` now registers the worker with `scope: '/antPOS/'`. The browser
only honours a wider-than-default scope when the worker's own response carries
the `Service-Worker-Allowed` header, so add this to the site's nginx config:

```nginx
location = /assets/ant_pos/antPOS/sw.js {
    add_header Service-Worker-Allowed "/antPOS/";
    add_header Cache-Control "no-cache";
    alias /home/frappe/frappe-bench/sites/assets/ant_pos/antPOS/sw.js;
}
```

Place it **before** the general `location /assets` block. Adjust the bench path.

Without this header the registration fails with:

> The path of the provided scope ('/antPOS/') is not under the max scope allowed
> ('/assets/ant_pos/antPOS/')

The app still works normally — you simply get no offline shell and no install
prompt. Nothing else depends on the worker.

### Verifying

1. Load `/antPOS`, open DevTools → Application → Service Workers. The worker
   should be listed with scope `/antPOS/` and status "activated and is running".
2. Application → Manifest should show no errors and offer "Install".
3. `scope` is `/antPOS/` and `start_url` is `/antPOS/` — note the trailing
   slash on both. A `start_url` of `/antPOS` is *outside* scope `/antPOS/` and
   Chrome rejects the whole manifest.

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
