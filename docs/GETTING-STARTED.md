# antPOS — installation, setup and first sale

A complete walkthrough from an empty bench to a printed invoice.

> Screenshots are marked `[screenshot: …]`. They need a running instance, so they
> are listed rather than embedded — see [Screenshots to capture](#screenshots-to-capture).

---

## 1. Prerequisites

| | |
|---|---|
| Frappe | v15 (15.111 or later, as ERPNext requires) |
| ERPNext | v15 — **required**, `hooks.py` declares it and the API imports from it |
| Python | 3.10+ |
| Node | 18+ (20 recommended) |

antPOS writes standard **Sales Invoices**, not POS Invoices, so there is no POS
Closing Entry step. It has its own shift documents instead: *Ant Opening Shift*
and *Ant Closing Shift*.

---

## 2. Install

```bash
cd ~/frappe-bench

bench get-app --branch version-15 erpnext
bench get-app https://github.com/anthertech/antPOS.git

bench --site yoursite.localhost install-app erpnext   # if not already
bench --site yoursite.localhost install-app ant_pos

bench --site yoursite.localhost migrate
bench build --app ant_pos
```

`install-app` runs `before_install`, which creates two roles — **POS Cash** and
**POS Billing** — and writes a Custom DocPerm matrix for them.

`migrate` applies the custom fields (`fixtures/custom_field.json`) and the
patches, including the indexes on `Sales Invoice.custom_ant_opening` and
`Payment Entry.reference_no`. On a site with a large invoice history the index
patch can take a few minutes; run it during a quiet window.

### Offline / installable PWA

One nginx change is required and cannot be made from inside the app. See
[DEPLOYMENT.md](DEPLOYMENT.md). Without it the app works normally, but there is
no offline shell.

---

## 3. Setup

Five things must exist before a cashier can open a shift. Missing any one of them
is the usual cause of "the POS won't open".

### 3.1 Company and warehouse

Standard ERPNext setup. Note the warehouse — the POS Profile points at it, and
every stock, batch and serial lookup is scoped to it.

### 3.2 Mode of Payment — **with a company account**

For each mode you intend to accept, open **Mode of Payment** and add a row to
*Accounts* for your company with a *Default Account*.

This matters: antPOS sends only the mode of payment and lets the server resolve
the ledger. A mode with no row for the company has nothing to resolve to and the
payment will fail.

`[screenshot: Mode of Payment with a company account row]`

### 3.3 Customer group and customers

Create the customer group your POS will sell to, and at least one customer in it.
The POS Profile restricts the cashier's customer list to the groups you list on
it, so a customer outside those groups will not appear.

### 3.4 POS Profile

**POS Profile** is where nearly all behaviour is configured.

Required:

| Field | Note |
|---|---|
| Company | |
| Warehouse | scopes all stock, batch and serial lookups |
| Currency | |
| Selling Price List | items are priced from this list (Selling Settings' default if empty) |
| Cost Center | |
| Disable Rounded Total | the invoice is not rounded; the cashier collects the grand total |
| Write Off Account / Cost Center / Limit | ERPNext requires these |
| **Payments** | one row per mode; tick *Default* for the one that should pre-fill |
| **Applicable for Users** | **the cashier must be listed here** (System Managers may use any profile) |
| Customer Groups | limits the customer dropdown |

> **Applicable for Users is not optional.** The app tile only appears for users
> who are on a POS Profile (`user_has_posprofile`), and the profile list is
> filtered the same way. A user who is not listed sees no POS at all.

`[screenshot: POS Profile — general tab]`
`[screenshot: POS Profile — payments and applicable users]`

#### antPOS-specific settings

These are custom fields added by the app and control real behaviour:

| Field | Effect |
|---|---|
| `Allow Credit` | permit submitting with less paid than the total; the rest is left outstanding |
| `Allow Partial Payments` | with credit allowed, permit paying part of the total; without it a credit sale is paid in full or not at all |
| `New items on new line` | scanning the same item twice adds a second line instead of incrementing qty |
| `Use Percentage Discount` | discount entry is a percentage rather than an amount |
| `Allow Item Name in Item Search` | search matches `item_name`, not just codes and barcodes |
| `Allow Create Sales Order` | show the Sale / Sales order choice above the cart |
| `Default Sales Order` | create a Sales Order alongside the invoice |

#### Item list

The *antPOS Item List* section controls the items shown beside the cart:

| Field | Default | Effect |
|---|---|---|
| `Show Item List` | on | show the browsable list; off leaves just the scan box |
| `Items to Load` | 50 | how many items are listed (1–500); search still finds any item |
| `Most Moving Items` | 8 | best sellers shown above the list; 0 hides that section |
| `Most Moving Period (Days)` | 30 | sales from this many days in the profile's warehouse rank them |
| `Cache Item List` | on | serve the list from cache for this profile |
| `Cache Duration (Minutes)` | 10 | how long the cache is kept (1–1440) |

The standard *Item Groups*, *Hide Unavailable Items* and *Hide Images* options
on the same profile also apply.

The cache is cleared automatically whenever an Item, an Item Price or the POS
Profile is saved, and a cashier can press **Refresh** under the list. Stock
quantities are *not* a reason to clear it (every sale would), so the quantity
shown on a card can be up to *Cache Duration* old; the cart still checks stock
when the item is added.

"Most moving" counts stock leaving the profile's warehouse through Sales
Invoices, POS Invoices and Delivery Notes. Transfers and material issues are
not sales and are ignored.

`[screenshot: POS Profile — antPOS settings section]`

### 3.5 Cashier user

Create the user and give them **POS Cash** (sell, submit, take payments) or
**POS Billing** (draft invoices only, no submit). Then add them to the POS
Profile's *Applicable for Users*.

---

## 4. Demo data

To get a working environment without doing any of the above by hand:

```bash
cd ~/frappe-bench
env/bin/python apps/ant_pos/test-data/seed_antpos.py yoursite.localhost
```

This creates a stocked warehouse, customers, payment modes with company
accounts, a POS Profile, an open shift, and four items covering every tracking
mode — plain, batch, serial, and batch + serial — each with a scannable barcode.
It prints the barcodes and serial numbers when it finishes.

See [test-data/README.md](../test-data/README.md). Remove it again with
`--teardown`.

---

## 5. First sale

Open **`/antPOS`**, or click the antPOS tile on the apps screen.

### 5.1 Open a shift

On first load you are asked to open one: pick a company and POS Profile, then
enter the opening float for each payment mode.

A cashier may have only one shift open at a time.

`[screenshot: Open Shift dialog]`

### 5.2 Select a customer

Nothing can be scanned until a customer is chosen — the scan is rejected with
*"Customer is required"*. Search by name or mobile number, or create one with the
**+** button.

`[screenshot: customer autocomplete with search]`

### 5.3 Add items

Tap an item in the list on the left, or type or scan into the search box.
Typing filters the list as you go; **Enter** looks the text up as a barcode,
serial or batch number. On a phone, the list opens from the grid button next to
the search box and stays open so you can add several items.

Scanning resolves, in order: **barcode → serial
number → batch number → item code**, then item name if
*Allow Item Name in Item Search* is on.

Expand a line with the chevron to edit quantity, rate and discount, or to pick a
batch or serial number. Batch and serial dropdowns only load for items that are
actually tracked.

`[screenshot: cart with a plain, a batched and a serialised line]`

### 5.4 Take payment

**Pay** moves to the payment screen. Amounts pre-fill on the default mode; click
a mode's button to move the full amount onto it, or type split amounts.

Paying more than the total is always allowed; the difference is shown as change
to give and recorded on the invoice. Paying less depends on *Allow Credit* and
*Allow Partial Payments* (see 3.4).

`[screenshot: payment screen with a split across two modes]`

### 5.5 Submit and print

**Submit** writes and submits the Sales Invoice. **Submit & Print** also opens
the browser's print dialog for it, using the profile's print format and
letterhead. Printing happens in the page itself, so popup blockers do not stop
it.

`[screenshot: printed invoice]`

---

## 6. Other workflows

| Action | Where | What it does |
|---|---|---|
| **Hold** | Save without submitting | leaves a draft; reopen from *Held* |
| **Held** | sidebar | list of drafts for this profile; opening one loads it back into the cart |
| **Return** | sidebar | pick a submitted invoice; a credit note is prepared with its lines and serials |
| **Payments** | sidebar | collect against outstanding invoices, or take an advance |
| **Close Shift** | sidebar | reconcile counted cash against expected, then submit |

### Closing a shift

*Close Shift* shows, per payment mode, the opening float, the expected total
(float + everything taken during the shift) and a field for what you actually
counted. The difference is calculated for you.

Submitting creates an **Ant Closing Shift** listing every invoice (returns
included) and payment in the shift, and marks the opening shift *Closed*.
Cashiers can only open and close their own shifts; System and Sales Managers
can act for anyone. Cancelling the closing entry reopens the shift, unless the
cashier has opened a newer one.

`[screenshot: Close Shift reconciliation]`

---

## 7. Troubleshooting

| Symptom | Cause |
|---|---|
| No antPOS tile on the apps screen | the user is not in any POS Profile's *Applicable for Users* |
| "Open Shift" dialog has no profiles | same — the profile list is filtered by that table |
| Cannot select a customer | the customer is not in a customer group listed on the POS Profile |
| Payment fails on submit | the Mode of Payment has no *Accounts* row for this company |
| Batch dropdown is empty | no batch of that item has stock in the profile's warehouse, or every batch has expired |
| "Serial No … not available in warehouse" | the serial exists but is not Active in that warehouse |
| Print dialog shows the wrong layout | the POS Profile has no *Print Format*, so the doctype's default is used |
| Cannot install as an app | the site is not on HTTPS (or `localhost`); see [DEPLOYMENT.md](DEPLOYMENT.md) |
| "Only open a shift for yourself" / "not a user of POS Profile" | the shift is for another user, or the cashier is not in *Applicable for Users* |
| Sales refused with "Credit is not allowed" | less was entered than the total and the profile does not allow credit |

---

## Screenshots to capture

For whoever has an instance running — capture these at 1440×900, light theme,
using the demo data so the content is consistent:

- [ ] `docs/images/open-shift.png` — Open Shift dialog, company and profile chosen
- [ ] `docs/images/customer-select.png` — customer autocomplete, mid-search
- [ ] `docs/images/cart.png` — three lines: plain, batched (expanded), serialised
- [ ] `docs/images/payment.png` — payment screen, amount split across two modes
- [ ] `docs/images/close-shift.png` — reconciliation with a deliberate difference
- [ ] `docs/images/pos-profile-general.png`
- [ ] `docs/images/pos-profile-payments.png`
- [ ] `docs/images/pos-profile-antpos-settings.png` — the custom fields section
- [ ] `docs/images/mode-of-payment.png` — the company accounts row
- [ ] `docs/images/held.png` — held invoices list
- [ ] `docs/images/return.png` — return invoice picker

Then replace each `[screenshot: …]` marker above with `![alt](images/name.png)`.
