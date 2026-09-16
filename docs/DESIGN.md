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
`pages/Pos.vue`. It watches the cart lines, so a line added from the mobile
item grid (where no cart line component is mounted) still gets server totals.
Its emitter listeners are removed on unmount.

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

The Held and Return dialogs share `pos/InvoicePicker.vue`: search, one card
per invoice (number, customer, date, amount), load more, and double-click to
open. The Payments page stacks on mobile, and Record payment is pinned to the
bottom.

### Shell

- **Sidebar** follows frappe-ui 0.1.278's `Sidebar`: 240px wide, or a 48px
  icon rail when collapsed; the header is a dropdown (logo, brand name, user)
  that turns white and raised while open; items are ghost buttons, the active
  one white with a light shadow (`bg-surface-selected`); labels fade out on
  collapse and the rail shows tooltips; a `panel-right-open` control at the
  bottom toggles and remembers the state. It lives in
  `components/Sidebar.vue` and `components/SidebarLink.vue` as a port of the
  stock component: below 1024px the rail is forced and the toggle hidden,
  because the POS switches to its stacked layout there and a 240px sidebar
  leaves too little room. The stock `<Sidebar>` only forces the rail below
  640px and keeps its toggle visible when forced.
- **Navbar**: white, 48px, page title, sale-state badge, profile badge.

Heights used to be percentages of flex containers (`h-[94%]`, `h-[80%]`,
`w-[18.4%]`); they are now flex with `min-h-0`, so the cart list is the only
thing that scrolls.

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
