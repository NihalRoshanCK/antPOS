# Changelog

## 0.2.0 — 2026-09-17

Run `bench --site <site> migrate` after upgrading; see
[Upgrading to 0.2.0](docs/DEPLOYMENT.md#upgrading-to-020).

### Added

- **Item list beside the cart**, cached per POS Profile, with the profile's
  most moving items first. Tap to add; typing in the scan box filters it; on
  phones it opens as a sheet. New *antPOS Item List* settings on POS Profile
  set how many items load, how many most-moving items show and over what
  period, and whether and how long the list is cached.
- **Forms built from layouts.** The New customer dialog and the cart line
  details come from the server; System Managers rearrange them in place
  (tabs, sections, columns, field settings) with a preview.
- **Settings:** Profile (name, contact, language, time zone, password),
  Preferences (theme), POS profile and Brand. The brand name and icon are used
  for the browser tab.
- Light, dark and automatic themes, shared with the desk's `desk_theme`.
- Resizable panes on desktop; a phone layout with a bottom tab bar.
- Installable as an app (PWA) without web server configuration.
- An antPOS workspace in the desk and a tile on `/apps` for POS users.

### Changed

- Signing in uses Frappe's login page, which returns to the POS; an expired
  session is sent there too. The app's own login page is removed.
- Items are priced from the POS Profile's price list (it was always
  *Standard Selling*), including customer-specific prices.
- The POS Profile's *Disable Rounded Total* now applies to the invoice.
- Paying more than the total is always allowed and recorded as change.
  *Allow Partial Payments* now governs paying part of a credit sale.
- Printing opens the print dialog in the page, so popup blockers no longer
  stop it.
- The Sale / Sales order choice moved from the header into the cart.
- frappe-ui 0.1.177 → 0.1.278.

### Security

- The installer no longer takes permissions away from ERPNext's roles; a patch
  repairs sites installed with 0.1.0. POS roles are read-only on masters.
- Shifts: only the cashier (or a System or Sales Manager) can open or close
  one, on a POS Profile that lists them; `create_opening` ignores anything but
  the company, profile and opening amounts.
- `scan_barcode` and `items` check Item, Customer and POS Profile access.
- Removed unused whitelisted methods, one of them open to guests.

### Fixed

- Shifts containing a return could not be closed.
- With rounding disabled every sale was refused; overpaying was refused when
  partial payments were off.
- Recording a payment on the Payments page always failed ("Target Exchange
  Rate is mandatory").
- Double taps on Pay, Hold sale, Save & print, Submit or Record payment could
  create duplicate documents.
- A missing serial number showed a message but did not stop the save.
- A new POS Cash user never saw Pay or Save & print: their "own documents
  only" permission was read as no permission until they owned a draft.
- Close Shift expected the cash tendered, not the cash kept: change handed
  back is now taken off.
- Opening `/antPOS/payments` directly bounced the user away.
- Failures opening a shift or loading permissions were silent.
- Stale totals after edits, amount discounts, and quick-entry required fields.

### Internal

- Ruff (Frappe's settings), prettier and eslint, with pre-commit hooks and a
  CI lint job; the code base is formatted.
- Clearing the item list cache no longer scans Redis keys.
- Tests: 95, covering the fixes above.

## 0.1.0

First release after a full security, correctness and performance audit. See
`docs/AUDIT-2026-09-16.md` for the findings this release addresses and
`docs/DEPLOYMENT.md` for the one change that must be made outside the app.

### Security

- `save_fields_layout` was whitelisted with `ignore_permissions=True` and no role
  check: any authenticated user could rewrite the field layout shown to every
  cashier. It is now System Manager only.
- `get_fields_layout`, `get_sidepanel_sections` and `get_doc_field` accepted an
  arbitrary doctype with no permission check. All three are now gated.
- `get_users` returned every User row (name, email, type) to any caller on every
  app load. Unprivileged callers now receive only their own record.
- `scan_barcode` fetched `Item` with `["*"]`, exposing `valuation_rate`,
  `last_purchase_rate` and `standard_rate` to cashiers. Replaced with an explicit
  ten-field projection.
- `calculate_invoice_item_taxes` instantiated a client-supplied doctype with
  `ignore_permissions=True`. The doctype is now pinned and permissions enforced.
- Production sourcemaps (22 files, 15 MB) are no longer built or published.

### Fixed

- **Item scanning:** `"\n".join(selected_serial_no)` was applied to a string or
  `None`. Scanning a non-serialised item raised `TypeError` (HTTP 500); scanning
  a serialised one turned `SN001` into `S\nN\n0\n0\n1`.
- **Payments:** `paid_from` and `paid_to` were hardcoded to `Debtors - FITPL` and
  `MGR Cash - FITPL`. Accounts are now resolved server-side, scoped to company.
- **Payments:** the shift total counted draft and cancelled Payment Entries, and
  the account-currency lookup read `paid_from`'s currency into `paid_to`.
- **Close Shift** could not be saved: `Ant Closing Shift` declared `amended_from`
  twice, and the mandatory `pos_profile` was never populated.
- `AntClosingShift.get_opening_shift()` filtered on `user`, a column that does not
  exist on `Ant Opening Shift` (the field is `cashier`).
- Closing a shift never wrote back `ant_closing_shift_detail`, and cancelling a
  closing entry never reopened the shift.
- Advance Payment Entries carried no `reference_no`, so they never appeared in
  shift totals.
- Every return invoice was assigned the same hardcoded temporary document name.
- Printing and follow-up payments used the pre-save temporary name, so the print
  URL 404'd and advance payments referenced a non-existent invoice.
- `saveAndSubmit` submitted even when the save had failed, creating a second
  document instead of submitting the first.
- `get_user_permissions` returned the `if_owner` flag of an arbitrary first row,
  so multi-role users got a result that depended on row ordering.
- `get_sidepanel_sections` referenced `"CAntpos Fields Layout"` and always raised.
- Opening-shift period validation was guarded on a field that is always empty on
  a new document, so it never ran; the duplicate-shift check did not exclude the
  document itself.
- The customer-group restriction from the POS Profile was captured before the
  profile had loaded and was therefore always empty.
- A failed customer creation reported nothing to the user.

### Performance

- Deployed assets: **23 MB to 6.6 MB**. Fonts: **73 files / 8.6 MB to 37 / 4.2 MB**
  (the app imported its own copy of Inter on top of the one frappe-ui ships).
- The single 2,113 kB bundle is split into app and vendor chunks; the app entry is
  now **15 kB**, so a release no longer invalidates 2.1 MB of client cache.
- Indexed `Sales Invoice.custom_ant_opening` and `Payment Entry.reference_no`, the
  sole predicates of the shift-close and payments queries.
- Three list queries used `pageLength: Number.MAX_VALUE * 2` (every customer,
  every open invoice, every serial number per cart line). Customer lookup is now
  searched server-side.
- `get_pos_transactions` LEFT JOINed the tax table, fanning out to one row per
  (invoice x tax line) and de-duplicating in Python. Now two queries aggregating
  in SQL, with grouping semantics unchanged.
- `get_pos_profiles_by_company` ran one query per POS Profile.
- Removed `frappe.db.commit()` from the page-render path.

### PWA

Previously non-functional in three independent ways, all fixed:

- `start_url` sat outside `scope`, so the manifest was rejected and the app could
  not be installed.
- Manifest icons pointed at a directory that did not exist, under the wrong app
  slug. Icons are now generated into `ant_pos/public/manifest/`.
- `index.html` referenced 30 splash screens from that same missing directory: 30
  failed requests on every cold iOS load.
- The service worker is registered with scope `/antPOS/`. This additionally needs
  a `Service-Worker-Allowed` header from nginx; see `docs/DEPLOYMENT.md`.

### Internal

- CI now installs the app on a real site with ERPNext, runs `bench migrate`,
  executes the test suite and enforces a bundle-size budget. It previously cloned
  the app from GitHub rather than testing the checked-out ref, and only ran a
  build.
- Replaced four empty `FrappeTestCase` stubs with tests covering the bugs above.
- Removed dead code: `SalesInvoice.vue` (fully commented out, referenced
  nowhere), the empty `utils/employee.py`, and unused imports.
