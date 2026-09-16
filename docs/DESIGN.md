# antPOS design notes

The reference renders are in `images/design-desktop.png` and
`images/design-mobile.png`.

## What this interface is

A counter terminal, used for whole shifts, often on a touch screen, often viewed
at a glancing angle. The job is: get items in, take money, don't make mistakes.
It is not a marketing surface, and it is not a dashboard. Every decision below
follows from that.

## Tokens

Defined in `tailwind.config.js` under `pos.*`.

| Token | Value | Use |
|---|---|---|
| `pos-page` | `#F4F5F7` | app background |
| `pos-line` | `#E3E6EA` | hairline structure |
| `pos-line2` | `#CFD5DD` | scrollbars, disabled marks |
| `pos-ink` | `#12161C` | primary text |
| `pos-ink2` | `#5A6472` | secondary text |
| `pos-ink3` | `#8B95A3` | meta, placeholders |
| `pos-readout` | `#171C24` | the totals panel |
| `pos-pay` | `#0B7A4B` | the Pay action, and nothing else |
| `pos-ret` | `#C2410C` | return and remove |
| `pos-warn` | `#B45309` | return-mode banner |

## Decisions

**Structure comes from hairlines, not shadows.** The app previously put
`shadow-2xl` on every panel. Stacked shadows read as mud at the angle a counter
screen is actually viewed from, and they made every panel look equally important.
One-pixel borders and a background tint carry the same structure and stay legible.

**One dark readout, and the total is the only large number.** The total is the
most-looked-at value in the app, so it gets the only inverted surface and the only
large type. Items / Net / Tax / Discount sit beside it at a quarter of the size.
Everything else on screen stays quiet so this reads from arm's length.

**Tabular lining numerals on every money value** (`.num` in `index.css`). Amounts
sit in columns that must align, and totals recalculate on every keystroke —
proportional figures make the digits jitter as they change. This is the one
typographic flourish the interface gets.

**One typeface.** Inter, already loaded. A display face would be wrong for
something stared at for eight hours, and the app does not need a voice — it needs
to be read quickly.

**Green means Pay, and only Pay.** Colour is reserved for actions with
consequences: green to take money, burnt orange to return or remove, amber for
return mode. Nothing else is coloured, so the coloured things mean something.

## Layout (issue #19)

`useBreakpoint()` splits at **1024px**, and `pages/Pos.vue` picks a layout:

- **`layouts/DesktopLayout.vue`** — scan pane left (30%, 280–380px), cart right.
- **`layouts/MobileLayout.vue`** — stacked: scan on top where the caret lands,
  cart in the middle, totals and Pay pinned in the thumb zone.

Both compose the same components; neither duplicates logic. `ItemSelector` takes
a `compact` prop for the mobile variant.

Sizes were previously percentages of a flex container (`h-[94%]`, `h-[80%]`,
`h-[20%]`, `w-[18.4%]`), which do not compose and left a 6% gap under the app
shell. They are now flex plus `min-h-0`, so the cart is the only thing that
scrolls.

**Touch targets are 44px minimum** on mobile: the qty stepper, the remove button
and every action. Desktop rows stay at 48px.

## Cart lines

Desktop uses a real CSS grid (`1fr 84px 96px 112px 32px`) so Qty, Rate and Amount
align down the column — it was a row of `w-[18.4%]` divs. Mobile drops columns
entirely for a card with a stepper, because four numeric columns do not fit at
390px.

Each line carries one quiet metadata line — code, UOM, batch, expiry, serial —
instead of surfacing five read-only fields in the expanded panel.

## Copy

Sentence case, not `HELD` / `RETURN` / `SAVE/NEW` / `PAY`. Buttons say what
happens: **Pay 612.68** carries the amount, so the cashier confirms the figure on
the control they are pressing.

**Held** and **Hold** used to sit side by side meaning different things — a list
and a verb. The list now shows a count and the verb reads **Hold this sale**.

Empty states direct rather than decorate: with no customer the cart says "Choose
a customer, then scan a barcode"; with one, "Scan a barcode to start the sale."

## Not done

- **The scan pane still has no product grid.** It shows recent scans and a scan
  hint. A browsable catalogue needs a new endpoint (items by group, with images,
  paginated, scoped to the profile's price list) and should be designed against
  real inventory.
- **The ported Vue has not been seen running.** The renders above are from a
  static prototype. The build compiles, but no site was available to verify the
  live app — check it before shipping.
