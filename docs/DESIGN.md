# antPOS design notes

Screenshots are from the running app (site with the `test-data` seed), not a
mock-up:

| | Before | After |
|---|---|---|
| Desktop | `images/before-desktop.png` | `images/pos-desktop.png`, `images/pos-desktop-empty.png` |
| Mobile | `images/before-mobile.png` | `images/pos-mobile.png`, `images/pos-mobile-empty.png` |
| Sidebar | | `images/sidebar-expanded.png`, `images/sidebar-menu.png`, `images/sidebar-collapsed.png` |

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

- **Sidebar** follows frappe-ui 0.1.278's `Sidebar`: 240px wide, or a 48px
  icon rail when collapsed; the header is a dropdown (logo, brand name, user)
  that turns white and raised while open; items are ghost buttons, the active
  one white with a light shadow (`bg-surface-selected`); labels fade out on
  collapse and the rail shows tooltips; a `panel-right-open` control at the
  bottom toggles and remembers the state. It is ported into
  `components/Sidebar.vue` and `components/SidebarLink.vue` rather than
  imported, because the installed frappe-ui (0.1.177) has an older revision of
  the component and upgrading frappe-ui affects every component the app uses.
  Below 1024px the rail is forced and the toggle is hidden, because the POS
  switches to its stacked layout there and a 240px sidebar leaves too little
  room. frappe-ui only forces the rail below 640px.
- **Navbar**: white, 48px, page title, sale-state badge, profile badge.

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
