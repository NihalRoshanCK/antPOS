# antPOS

A point of sale app for **ERPNext**, built with Frappe UI. It works on desktop,
tablet and phone, and can be installed as an app from the browser.

![antPOS on desktop](screenshots/pos-desktop.png)

## Features

- **Fast checkout:** scan barcodes, serial and batch numbers, or tap items from
  a list that shows the most moving items first.
- **Camera scanning:** scan barcodes and QR codes with the phone camera.
- **Payments:** split across payment methods, give change, sell on credit, and
  use customer advances.
- **Discounts and rates:** per line or for the whole sale, as the POS Profile
  allows.
- **Held sales and returns:** park a sale and pick it up later, or return items
  from a past invoice.
- **Sales orders:** create a Sales Order with the invoice when needed.
- **Shifts:** open and close cashier shifts with a cash count per payment
  method.
- **Standard ERPNext documents:** sales, returns and payments are normal Sales
  Invoices and Payment Entries.
- **Customisable forms:** admins can change the New customer form and the cart
  line details from the POS.
- **Themes:** light, dark and automatic.
- **Installable app (PWA)** for desktop, Android and iOS.

## Screenshots

| Payment | Held sales |
|---|---|
| ![Payment](screenshots/payment.png) | ![Held sales](screenshots/held.png) |

| Dark mode | Settings |
|---|---|
| ![Dark mode](screenshots/pos-desktop-dark.png) | ![Settings](screenshots/settings.png) |

| Items | Cart | Camera scan |
|---|---|---|
| ![Mobile items](screenshots/mobile-items.png) | ![Mobile cart](screenshots/mobile-cart.png) | ![Camera scan](screenshots/mobile-scanner.png) |

## Requirements

- Frappe and ERPNext v15

## Installation

```bash
cd ~/frappe-bench
bench get-app ant_pos https://github.com/anthertech/antPOS.git
bench --site yoursite.com install-app ant_pos
bench --site yoursite.com migrate
bench build --app ant_pos
```

Open `https://yoursite.com/antPOS`.

## Setup

1. **Mode of Payment:** add an account for your company to each payment method
   you want to use.
2. **POS Profile:** set the company, warehouse, price list and payment methods,
   and add your cashiers under *Applicable for Users*.
3. **Users:** give cashiers the **POS Cash** role (sell and take payments) or
   **POS Billing** (prepare sales only).
4. Open `/antPOS`, start a shift, pick a customer and start selling.

The camera and the installable app need the site to be served over HTTPS.

## Roles

| Role | Can do |
|---|---|
| POS Cash | Open and close their shift, sell, take payments, return and print |
| POS Billing | Prepare and hold sales for a cashier |
| System Manager | Everything above, plus POS settings, brand and form layouts |

## Contributing

Contributions are welcome.

1. Fork the repository and create a branch from `develop`.
2. Install the app on a local bench (see [Installation](#installation)).
3. Set up the checks once with `pre-commit install`. They run ruff for Python and
   prettier and eslint for the frontend on every commit.
4. Make your change and run the tests:

   ```bash
   bench --site yoursite.localhost run-tests --app ant_pos
   ```

5. Open a pull request against `develop` with a short description of the change.

Found a bug or have an idea? [Open an issue](https://github.com/anthertech/antPOS/issues).

## Support

- Issues: [github.com/anthertech/antPOS/issues](https://github.com/anthertech/antPOS/issues)
- Email: [support@anthertech.com](mailto:support@anthertech.com)

## Built with

- [Frappe Framework](https://frappe.io/framework)
- [ERPNext](https://frappe.io/erpnext)
- [Frappe UI](https://ui.frappe.io)

## License

antPOS is released under the [MIT License](license.txt).

Copyright (c) 2024 Anther Technologies Pvt Ltd
