# antPOS design notes

Screenshots are from the running app (site with the `test-data` seed), not a
mock-up:

| | Before | After |
|---|---|---|
| Desktop | `images/before-desktop.png` | `images/pos-desktop.png`, `images/pos-desktop-empty.png` |
| Mobile | `images/before-mobile.png` | `images/mobile-items.png`, `images/mobile-cart.png`, `images/mobile-held.png`, `images/mobile-payments.png` |
| Sidebar | | `images/sidebar-expanded.png`, `images/sidebar-menu.png`, `images/sidebar-collapsed.png` |

## Principle: stay inside frappe-ui

antPOS runs inside Frappe and is built on frappe-ui. The POS uses frappe-ui's
own semantic tokens (`surface-*`, `outline-gray-*`, `ink-gray-*`) and its
`Button`, `Badge`, `FormControl` and `Autocomplete` components, so it looks like
part of the same product as the desk.

An earlier pass invented a separate palette with a dark "readout" panel. On the
live app it clashed with the frappe shell and turned an idle screen into a black
slab reading 0.00. It was removed; do not reintroduce a private palette.

## frappe-ui version

The app is on **frappe-ui 0.1.278** (pinned in both `package.json` files).
Things that changed on the way up from 0.1.177 and matter here:

- Imports are limited to the package's exports. The Tailwind preset is
  `frappe-ui/tailwind` and the stylesheet `frappe-ui/style.css`.
- `toast.create` takes `{ message, type, duration, icon: Component }`; `title`,
  `timeout`, `position` and icon names are gone. `utils/index.js`
  (`createToast`, `showToast`) translates the old call shape.
- The stylesheet no longer sets a base text colour; `index.css` does.
- Don't give frappe-ui its own Rollup chunk: it and the general vendor chunk
  import each other and the app fails at startup ("Cannot access … before
  initialization").
- The customer picker uses frappe-ui's `Autocomplete`. The app's old copy of
  that component was removed.

## Themes

Light, dark and automatic, working the same way as the Frappe desk
(`frappe/public/js/frappe/ui/theme_switcher.js`):

- The choice is the user's **`desk_theme`** (Light / Dark / Automatic), saved
  through `frappe.core.doctype.user.user.switch_theme`. The desk and the POS
  share one setting.
- `<html data-theme-mode>` holds the choice and `<html data-theme>` the resolved
  scheme. frappe-ui's tokens and `dark:` variants key off `data-theme`.
- `www/antPOS.py` writes the choice onto `<html>` and an inline script in
  `index.html` resolves Automatic before first paint, so there is no white
  flash. Automatic then follows the OS setting live.
- **Switch Theme** is in the sidebar header menu (*Toggle theme*): three preview
  cards, *Frappe Light*, *Timeless Night* and *Automatic*, with arrow-key
  navigation. **Ctrl/Cmd+Shift+G** switches light/dark, as in the desk.

Dark mode only works if components use frappe-ui's semantic tokens. Raw colours
(`bg-white`, `text-gray-*`, `bg-black-overlay-*`, hex values) do not change with
the theme, so do not add them. The previous ones were replaced, and `showToast`
no longer forces a white background.

Reference: `images/pos-desktop-dark.png`, `images/theme-switcher.png`.

## Layout (issue #19)

`useBreakpoint()` splits at **1024px**; `pages/Pos.vue` picks a layout.

- **`layouts/DesktopLayout.vue`**: two white cards on the grey page, the scan
  pane (30%, 280–380px) and the cart.
- **`layouts/MobileLayout.vue`**: one screen at a time (below).

Both use the same components. `ItemSelector`, `ItemDetail` and `Invoice` take a
`compact` prop for the mobile variant.

Totals are recalculated by `composables/useInvoiceRecalc.js`, called once from
`pages/Pos.vue`:

- It watches a **cart signature**: lines (id, item, qty, rate, UOM, batch,
  discount, serial count), the customer, and the invoice discount. Any
  difference from the cart the current totals were computed for queues a
  request (300 ms debounce). This works whether or not the cart lines are on
  screen.
- Requests are numbered. A reply is applied only if it answers the newest
  request **and** the cart still has the signature it was built from.
  Anything else is dropped, because the change that made it stale has
  already queued a newer request. Replies used to be applied in arrival
  order, so a slow reply could set a quantity back (typed 5, ended at 2).
- Emptying the cart, or finishing or cancelling a sale, invalidates anything
  still in flight.

`composables/useCartTotals.js` is what the totals row, the phone cart bar and
the Pay button display:

- The item count and line amounts come from the lines, so they are right
  immediately.
- Net, tax, discount and total come from the server. While a recalculation
  is pending they are estimated by scaling the last server figures by the
  change in net, and are dimmed (`aria-busy`).
- Lines are removed by identity (`invoiceStore.removeLine`), not by position.

### Sale or sales order

When the POS Profile has "Allow Create Sales Order", the cart shows a
**Sale | Sales order** switch under the customer (`pos/SaleModeBar.vue`),
with a "Deliver by" date when Sales order is picked. The payment screen shows
the order and its date again, and the header badge reads "Order · …".

The choice belongs to the sale (`composables/useSaleMode.js`). Each new sale
starts from the profile's "Default Sales Order". The switch used to live in the
header and wrote into the profile itself, so one sales order turned every later
sale into one too. Returns never create an order.

### Server-driven forms

The **New customer** dialog and a cart line's **details** are built from a
layout the server sends (`ant_pos/api/form_layout.py`), not hard-coded fields.
The format and the editing flow follow Frappe CRM (`CRM Fields Layout`,
`QuickEntryModal`, `FieldLayoutEditor`):

| Form | Antpos Fields Layout |
|---|---|
| New customer | `Customer` / `Quick Entry` |
| Cart line details | `Sales Invoice Item` / `Grid Row` |

**Editing is done in place.** A System Manager on desktop sees a pencil
button:
- in the New customer dialog's header;
- beside an expanded cart line's fields.

It opens **Edit … layout** (`components/layout-editor/`):

- **Tabs:** drag to reorder; double-click to rename; ⋯ to rename or remove.
  One unlabelled tab means no tab bar.
- **Sections:** drag by the handle; double-click to rename. ⋯ has:
  - collapsible, hide label, hide border;
  - remove, or remove and move its columns to a neighbour;
  - move to the previous or next tab;
  - add or remove columns (up to four), or move the last column.
- **Columns:** dashed boxes that can be dragged between sections. **Add
  field** at the bottom of each column searches the DocType's fields.
- **Fields:** drag by the handle; × removes. The settings button (or a click
  on the label) sets label, default, required, read only and hidden.
- **Show preview** renders the unsaved layout as the server resolves it.
  **Reset** discards changes, **Save** stores the layout, and **Restore
  default** drops a custom layout. Saved layouts reach the open form at once,
  and other tabs when the cashier returns to them.

The New customer dialog steps aside while its layout is edited (as in CRM)
and comes back afterwards with what was typed. The desk form of Antpos
Fields Layout only shows the JSON and points to antPOS.

Rules the server enforces:

- Unknown fields are rejected on save. Unsupported field types (tables,
  attachments, HTML) are skipped. Older flat layouts are still read.
- Overrides can make a field required or read-only, never the reverse. A
  required field can be hidden only when it has a default.
- Quick entry adds any field the DocType requires that the layout left out,
  and `create_from_quick_entry` only accepts the layout's fields. Customer
  Mobile and Email are inputs there, since ERPNext creates the primary
  contact from them.
- Permission levels apply: fields without write access are read-only, and
  fields without read access are hidden.

`components/form/LayoutForm.vue` renders tabs, sections (with the options
above) and columns, and `FieldControl`/`LinkControl` render the fields. A
cart line applies its own rules on top of the layout:

- the rate follows "Allow User to Edit Rate";
- the discount fields follow the discount mode;
- item code, UOM, warehouse and price are always locked;
- batch and serial keep their own pickers.

### Resizable panes

As on Frappe CRM's record pages (`Resizer`), the desktop panes can be resized
by dragging the handle between them (`components/PaneResizer.vue`):

- Point of sale: item list | cart, and payment panel | cart (each has its
  own width).
- Payments: invoices | payment panel.

The width is remembered on the device. Double-click (or Enter) restores the
default, and the arrow keys resize (Shift for bigger steps). The other pane
always keeps a minimum width, and the cart's action bar wraps instead of
cutting off Pay. Phones have no handles.

### Mobile structure

There is no sidebar below 1024px. The app shell is a phone app:

- **Top bar** (`mobile/MobileTopBar.vue`): the screen title and the profile or
  customer. The cart and payment screens show a back arrow, and the bar shows
  the sale state (Not saved, Draft, Return).
- **Bottom tab bar** (`mobile/MobileTabBar.vue`): Sell, Held, Payments and More.
  It is hidden on the cart and payment screens, which have their own action
  bar.
- **More** (`mobile/MoreSheet.vue`, a `BottomSheet`): the user and shift, and
  the actions that used to be in the sidebar menu: Return an invoice, Close
  shift, Theme, Settings, Go to desk and Log out.

On the Sell tab, `stores/mobile.js` picks the screen:

1. **Items**: customer, search and the item grid. A cart bar at the bottom
   shows units and total, and opens the cart.
2. **Cart**: line cards with a 44px stepper, totals, Held, Return, Hold, Print,
   and Pay.
3. **Payment**: full screen. Back returns to the cart and leaves the draft
   editable.

Emptying the cart returns to Items. Opening a held sale or a return goes
straight to Cart.

Held and Return share `pos/InvoicePicker.vue` (`images/return-picker.png`,
`images/mobile-held.png`). On desktop it is a panel near the top of the screen;
on phones it is a full-height bottom sheet. Invoices are grouped by day (Today,
Yesterday, a date), and each row shows the customer, the invoice number and
time, the amount and the item count. Returns also show the payment status. One
tap opens a sale; that row shows a spinner and the others are disabled until it
loads. There is no Enter-to-open shortcut, because a debounced search could
open the wrong invoice. On phones, the loaded sale opens in the cart.
The Payments page stacks on mobile, and Record payment is pinned to the
bottom.

### Shell

The desktop shell follows Frappe CRM's `AppSidebar` (`components/Sidebar.vue`):

- **Width:** 220px, or a 48px icon rail when collapsed. The choice is
  remembered per browser.
- **Top:** the brand logo and name with the user's name. Its menu has:
  - **Apps**, a submenu with the Desk and every app on `/apps`;
  - **Settings**;
  - **Close shift**;
  - **Log out**, after a separator.
- **Middle:** the pages. `SidebarLink` uses CRM's row styling.
- **Foot:** the till's **POS profile card** (`PosProfileCard.vue`) and
  Collapse.
  - The card shows the profile, and a green dot with "Open since …" while a
    shift is open.
  - Its menu has *Profile and shift details* and *Close shift*.
  - The profile used to be an outline badge in the header; the header now
    only shows the sale state.

**Settings** (`components/Dialog/Settings.vue`) is laid out like CRM's:
grouped pages on the left (tabs across the top on a phone).

- *Preferences* (everyone): theme cards for Light, Dark and Automatic,
  shared with the desk. The previews use fixed colours, so each card shows
  its own scheme. Ctrl/Cmd+Shift+G still toggles the theme. The separate
  Theme dialog and menu items are gone.
- *POS profile* (everyone): the profile (warehouse, price list, currency,
  customer groups) and the open shift (cashier, dates, opening amounts),
  with Close shift and, for System Managers, Open in desk.
- *Brand* (System Managers): name, logo and favicon.

On phones, More → **Settings** opens the same dialog, and the user card at
the top of More opens the POS profile page.

## Item list

The left pane (`components/pos/ItemCatalog.vue`, `ItemCard.vue`) lists items
from `ant_pos.ant_pos.api.item_list.get_item_list`, most moving first. Cards are
compact, with a 40px thumbnail beside the text: most catalogues have few
product photos, and a large initials tile only halved how many items fit.
Cards show price, stock (amber when 5 or fewer, red and disabled when out,
unless the site allows negative stock) and batch/serial tags.

Tapping a card goes straight to the non-debounced add request, since the scan
path is debounced and quick taps would otherwise be dropped. Extra taps on an
item whose first add is still in flight are counted and applied to that line,
so a double tap gives one line with quantity 2.

On phones the list opens in a sheet from the grid button beside the search box.

Toasts are moved to the top right (`index.css`): frappe-ui puts them
bottom-right, on top of Pay.

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

- **The item list is not paginated.** It loads up to the profile's *Items to
  Load* (max 500) and relies on search beyond that.
- **Payments, dialogs (Held, Return, Close Shift, Customer form) and the login
  page were not restyled.** They still use the original markup.
