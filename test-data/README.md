# Local test data

`seed_antpos.py` builds a working POS environment on a local site so the app can
be exercised by hand.

It deliberately lives **outside** the `ant_pos` python package:

- it is not installed with the app and ships to no site;
- `bench execute ant_pos...` cannot reach it, so it cannot be run against
  production by accident;
- it only ever runs when someone points it at a site explicitly.

## Usage

Run from the **bench root**, using the bench's python:

```bash
cd frappe-bench

# seed
env/bin/python apps/ant_pos/test-data/seed_antpos.py mysite.localhost

# remove what it created
env/bin/python apps/ant_pos/test-data/seed_antpos.py mysite.localhost --teardown
```

Requires a site with `erpnext` and `ant_pos` installed and a Company set up.
Every helper is idempotent, so re-running is safe.

## What it creates

| | |
|---|---|
| Warehouse | `Stores - <abbr>`, stocked |
| Customers | `AntPOS Walk-in`, `AntPOS Regular` |
| Customer group | `AntPOS Retail` (the POS Profile is restricted to it) |
| Payment modes | `AntPOS Cash` (default), `AntPOS Card`, both with company-scoped accounts |
| POS Profile | `AntPOS Test Profile`, with the current user applicable |
| Opening shift | submitted and open, ₹500 opening cash |

### Items — one per tracking mode

| Barcode | Item | Tracking | Stock |
|---|---|---|---|
| `1000000000017` | `ANTPOS-PLAIN` | none | 100 |
| `1000000000024` | `ANTPOS-BATCH` | batch | `ANTPOS-BATCH-A` 40, `ANTPOS-BATCH-B` 25 |
| `1000000000031` | `ANTPOS-SERIAL` | serial | 3 (`ANTPOS-SN-0001..0003`) |
| `1000000000048` | `ANTPOS-BATCH-SERIAL` | batch + serial | 2 + 1 across two batches |

These four exist because `scan_barcode` takes a different code path for each, and
`items()` branches on `has_batch_no` / `has_serial_no`.

## Deliberate traps

The data is shaped to catch regressions in the bugs this app has had:

- **`ANTPOS-BATCH-EXPIRED`** holds stock but expired yesterday. It must **not**
  appear in the batch dropdown — if it does, `get_batches_list` has regressed.
- **Items carry a `valuation_rate` and `last_purchase_rate` different from their
  selling price.** Scan one and inspect the network response: neither value may
  appear. They used to, because the scan fetched `Item` with `["*"]`.
- **`ANTPOS-PLAIN` has no serial or batch.** Scanning it used to raise
  `TypeError` and return HTTP 500, because `"\n".join(None)` was unconditional.
- **Both payment modes have company-scoped accounts.** The Payments screen used
  to post to hardcoded `Debtors - FITPL` / `MGR Cash - FITPL`; with this data the
  accounts must resolve from the company instead.
- **The POS Profile is restricted to `AntPOS Retail`.** The customer dropdown
  must not offer customers outside that group — the restriction used to be
  captured before the profile loaded and was always empty.

## Manual checklist

Worth walking once after seeding, since these are the paths that were broken:

1. Scan `1000000000017` — item is added, no 500.
2. Scan `1000000000031` — one serial is selected, not split into characters.
3. Expand a batched line — the dropdown lists A and B, never EXPIRED, and
   available qty is non-zero (it used to always read 0).
4. Pay and print — the print window opens on a real invoice name, not
   `new-sales-invoice-…`.
5. Take a return — its draft name differs each time.
6. Close the shift — it saves, and the payment table shows date, amount and mode
   rather than blank columns.
