# Changelog

## Unreleased

### Added

- **Item list beside the cart**, cached per POS Profile, with the profile's
  most moving items first. Tap to add; typing in the scan box filters it; on
  phones it opens as a sheet. New *antPOS Item List* settings on POS Profile
  set how many items load, how many most-moving items show and over what
  period, and whether and how long the list is cached. The cache is cleared when
  an Item, Item Price or the POS Profile changes, or from the list's Refresh
  button.
- Light, dark and automatic themes, shared with the desk's `desk_theme`.

### Changed

- frappe-ui 0.1.177 → 0.1.278, with a sidebar matching its current design.
- Toasts appear at the top right instead of over the Pay button.

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
