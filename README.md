# 💼 antPOS

**antPOS** is a modern, efficient, and flexible Point of Sale (POS) system built on **Frappe** and **ERPNext**. Designed to work seamlessly across all Frappe versions, it leverages Frappe's built-in APIs and validation mechanisms to ensure smooth performance, accurate error handling, and a superior user experience.

---

## 🚀 Features

- 🧾 **Standard Sales Invoices**
  Sales, returns and payments are ordinary ERPNext documents; antPOS adds its
  own opening and closing shifts instead of POS Invoices and POS Closing.

- 🛒 **Fast checkout**
  Barcode, serial and batch scanning, an item list with the most moving items,
  discounts, split payments, change, credit sales and optional Sales Orders.

- 🧩 **Built with Frappe UI**
  Light, dark and automatic themes shared with the desk; resizable panes on
  desktop and a phone layout with a bottom tab bar.

- ⚙️ **Forms you can change from the POS**
  System Managers edit the New customer dialog and the cart line details in
  place, without code.

- 📱 **Installable app (PWA)**
  Installs from the browser on desktop, Android and iOS.

- 🔐 **Scoped access**
  POS Billing and POS Cash roles, POS Profile users, and cashiers who can only
  work in their own shifts.

---

## ✅ Requirements

- Frappe and ERPNext **v15**
- Python 3.10+, Node 18+ (20 recommended)

---

## 🛠️ Installation

```bash
cd ~/frappe-bench
bench get-app ant_pos https://github.com/anthertech/antPOS.git
bench --site yoursite.com install-app ant_pos
bench --site yoursite.com migrate
bench build --app ant_pos
```

Then open `https://yoursite.com/antPOS`.

---

## 📦 Usage

**[Getting Started](docs/GETTING-STARTED.md)** walks through installation, the
five things that must be configured before a cashier can open a shift, and a
first sale end to end.

Want a working environment immediately?

```bash
cd ~/frappe-bench
env/bin/python apps/ant_pos/test-data/seed_antpos.py yoursite.localhost
```

That creates a stocked warehouse, customers, payment modes, a POS Profile, an
open shift and four scannable items covering plain, batch, serial and
batch+serial tracking. See [test-data/README.md](test-data/README.md).

### Documentation

| | |
|---|---|
| [Getting Started](docs/GETTING-STARTED.md) | install, configure, first sale, troubleshooting |
| [Deployment](docs/DEPLOYMENT.md) | PWA, assets and upgrade notes |
| [Test data](test-data/README.md) | local demo data and a manual QA checklist |
| [Design](docs/DESIGN.md) | how the screens are built and why |
| [CHANGELOG](CHANGELOG.md) | what changed in each release |

---

## 🧑‍💻 Development

```bash
cd apps/ant_pos/AntPos
yarn install
yarn dev            # Vite dev server
yarn lint           # eslint
yarn format         # prettier
cd .. && ruff check . && ruff format .
bench --site yoursite.com run-tests --app ant_pos
```

`pre-commit install` runs the same checks on every commit
(`.pre-commit-config.yaml`).

---

## 🤝 Contributions

We welcome contributions from the community!  
Feel free to:

- Submit issues  
- Open pull requests  
- Suggest improvements

👉 [Contribute on GitHub](https://github.com/anthertech/antPOS)

---

## 📄 License

Ant-POS is released under the **MIT License** — free for personal and commercial use.

---

## 📬 Contact & Support

Have questions or need help? Visit our [GitHub repository](https://github.com/anthertech/antPOS) or [contact us](mailto:support@anthertech.com).

---

> 💡 *Ant-POS — built to simplify sales, powered by Frappe.*
