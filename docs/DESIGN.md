# antPOS design notes

Screenshots are from the running app (site with the `test-data` seed), not a
mock-up:

| | Before | After |
|---|---|---|
| Desktop | `images/before-desktop.png` | `images/pos-desktop.png`, `images/pos-desktop-empty.png` |
| Mobile | `images/before-mobile.png` | `images/pos-mobile.png`, `images/pos-mobile-menu.png` |

## Principle: stay inside frappe-ui

antPOS runs inside Frappe and is built on frappe-ui. The POS uses frappe-ui's
own semantic tokens (`surface-*`, `outline-gray-*`, `ink-gray-*`) and its
`Button`, `Badge`, `FormControl` and `Autocomplete` components, so it looks like
part of the same product as the desk.

An earlier pass invented a separate palette with a dark "readout" panel. On the
live app it clashed with the frappe shell and turned an idle screen into a black
slab reading 0.00. It was removed; do not reintroduce a private palette.

## Layout (issue #19)

`useBreakpoint()` splits at **1024px**; `pages/Pos.vue` picks a layout.

- **`layouts/DesktopLayout.vue`**: two white cards on the grey page, the scan
  pane (30%, 280–380px) and the cart.
- **`layouts/MobileLayout.vue`**: stacked with no card frames. Scan on top, cart
  lines as cards, totals and actions at the bottom.

Both use the same components. `ItemSelector` and `ItemDetail` take a `compact`
prop for the mobile variant.

### Shell

- **Sidebar**: on desktop a static column that collapses to a 56px icon rail
  (persisted). On mobile it is an off-canvas drawer with a backdrop, closed by
  default and closed again after navigating.
  The old sidebar used the same persisted flag for both, so on phones it stayed
  pinned open over the app, which clipped the search, the customer field and the
  action buttons.
- **Navbar**: white, 48px, page title, sale-state badge, profile badge. The
  hamburger only appears below 1024px.

Heights used to be percentages of flex containers (`h-[94%]`, `h-[80%]`,
`w-[18.4%]`); they are now flex with `min-h-0`, so the cart list is the only
thing that scrolls.

## Cart

- **Desktop lines** use a CSS grid (`1fr 84px 96px 112px 32px`) so Qty, Rate and
  Amount line up down the column.
- **Mobile lines** are cards with a 44px quantity stepper.
- Each line has one metadata row: code, UOM, batch, expiry, serial.
- **Expanded line** shows quantity, rate, discount % and discount amount. Batch
  controls appear only on batch-tracked lines and serial controls only on
  serialised ones. Available quantity and expiry are read-only (they used to be
  editable inputs). Fields duplicated by the metadata row (item code, UOM,
  stock UOM, group, net rate, serial count) were removed.
- **Money** uses tabular figures (`.num` in `index.css`) so digits line up and
  don't shift while totals recalculate.

## Footer

Totals summary (items, net, tax, discount, and the total in the largest type),
then actions:

- Desktop: `Held` (blue subtle) and `Return` (red subtle) on the left; `Hold
  sale`, `Save & print` and a green `Pay <amount>` on the right. The colours
  follow the original app.
- Mobile: four equal buttons (Held, Return, Hold, Print), then `Pay` full width.
  All targets are at least 44px.
- Actions that need items are disabled on an empty cart.

## Copy

Sentence case. `Pay` shows the amount. A held-sales list next to a "hold" verb
was confusing, so the verb reads **Hold sale**. The empty cart tells the cashier
what to do next.

## Not done

- **No product grid.** The scan pane shows recent scans and a scan hint. A
  browsable catalogue needs a new endpoint (items by group, images, paginated,
  scoped to the profile's price list).
- **Payments, dialogs (Held, Return, Close Shift, Customer form) and the login
  page were not restyled.** They still use the original markup.
