# 💼 antPOS

**antPOS** is a modern, efficient, and flexible Point of Sale (POS) system built on **Frappe** and **ERPNext**. Designed to work seamlessly across all Frappe versions, it leverages Frappe's built-in APIs and validation mechanisms to ensure smooth performance, accurate error handling, and a superior user experience.

---

## 🚀 Features

- ✅ **Supports All Frappe Versions**  
  Developed to be compatible with all Frappe and ERPNext versions.

- 🧩 **Built with Frappe UI**  
  Uses vanilla Frappe UI components for a seamless and efficient interface.

- 🧾 **Direct Sales Invoice Creation**  
  Creates standard **Sales Invoices** instead of POS Invoices, avoiding dependency on POS Closing.

- ⚙️ **Dynamic Field Configuration**  
  Configure fields dynamically and display them directly in the POS interface.

- 🔌 **Frappe API Integration**  
  Utilizes built-in Frappe APIs for real-time updates, validation, and error handling.

- 📱 **Mobile Compatibility (Upcoming)**  
  Future updates will include **Ionic integration** for a mobile-friendly experience.

---

## 🛠️ Installation

Follow these steps to install Ant-POS on your ERPNext setup:

```bash
# Step 1: Navigate to your Frappe bench directory
cd ~/frappe-bench
```

```bash
# Step 2: Clone the Ant-POS app from GitHub
bench get-app ant_pos https://github.com/anthertech/antPOS.git
```

```bash
# Step 3: Install the Ant-POS app on your site (replace 'yoursite.com' with your actual site name)
bench --site yoursite.com install-app ant_pos
```

```bash
# Step 4: Migrate your site (replace 'yoursite.com' with your actual site name)
bench --site yoursite.com migrate 
```

```bash
# Step 5: Build site assets (recommended after installing a new app)
bench --site yoursite.com build
```

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
| [Deployment](docs/DEPLOYMENT.md) | the nginx header the PWA needs, asset and index notes |
| [Test data](test-data/README.md) | local demo data and a manual QA checklist |
| [CHANGELOG](CHANGELOG.md) | what changed in 0.1.0 |

---

## 🔮 Future Enhancements

- 📱 **Mobile-Friendly Interface**  
  Integration with **Ionic** to deliver a sleek mobile experience.

- 🛠 **Advanced Customization**  
  More settings for deeper customization of the POS workflow.

- ⚡ **Performance Improvements**  
  Optimized database queries and background processes for faster checkouts.

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
