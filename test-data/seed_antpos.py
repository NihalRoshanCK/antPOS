#!/usr/bin/env python
"""Local test data for antPOS.

This file lives OUTSIDE the ant_pos python package on purpose. It is not
installed with the app, does not ship to any site, and cannot be reached with
`bench execute` -- so there is no way to run it against production by accident.

Run it from the bench root against a local site:

    cd frappe-bench
    env/bin/python apps/ant_pos/test-data/seed_antpos.py <site>          # seed
    env/bin/python apps/ant_pos/test-data/seed_antpos.py <site> --teardown

It builds a complete, clickable POS environment: a warehouse with stock, four
items covering every tracking mode the scanner supports, customers, payment
modes, a POS Profile and an open shift.

Every helper is idempotent -- it returns the existing record if one is already
there -- so re-running is safe.
"""

import os
import sys

import frappe
from frappe.utils import add_days, today

# --- Names. Kept distinctive so demo data is obvious in a shared site. ---
COMPANY_ABBR = "WP"  # erpnext's before_tests creates "Wind Power LLC"
WAREHOUSE = "Stores"
CUSTOMER_GROUP = "AntPOS Retail"
TERRITORY = "AntPOS Territory"
CUSTOMER = "AntPOS Walk-in"
SECOND_CUSTOMER = "AntPOS Regular"
POS_PROFILE = "AntPOS Test Profile"
MODE_CASH = "AntPOS Cash"
MODE_CARD = "AntPOS Card"

ITEM_GROUP = "AntPOS Test Items"

# The four tracking modes scan_barcode has to distinguish between.
ITEM_PLAIN = "ANTPOS-PLAIN"
ITEM_BATCH = "ANTPOS-BATCH"
ITEM_SERIAL = "ANTPOS-SERIAL"
ITEM_BATCH_SERIAL = "ANTPOS-BATCH-SERIAL"

BARCODE_PLAIN = "1000000000016"
BARCODE_BATCH = "1000000000023"
BARCODE_SERIAL = "1000000000030"
BARCODE_BATCH_SERIAL = "1000000000047"

BATCH_A = "ANTPOS-BATCH-A"
BATCH_B = "ANTPOS-BATCH-B"
BATCH_EXPIRED = "ANTPOS-BATCH-EXPIRED"

SERIALS_PLAIN = ["ANTPOS-SN-0001", "ANTPOS-SN-0002", "ANTPOS-SN-0003"]
SERIALS_IN_BATCH_A = ["ANTPOS-BSN-0001", "ANTPOS-BSN-0002"]
SERIALS_IN_BATCH_B = ["ANTPOS-BSN-0003"]

PRICE_LIST = "Standard Selling"
DEFAULT_RATE = 100.0


# ---------------------------------------------------------------- bootstrap --


def setup_pos_environment():
	"""Create everything the POS needs, in dependency order."""
	company = get_company()

	create_item_group()
	warehouse = create_warehouse(company)
	create_customer_group()
	create_territory()
	create_customer(CUSTOMER)
	create_customer(SECOND_CUSTOMER)

	create_mode_of_payment(MODE_CASH, company, account_type="Cash")
	create_mode_of_payment(MODE_CARD, company, account_type="Bank")

	create_items()
	receive_stock(company, warehouse)
	create_pos_profile(company, warehouse)

	return frappe._dict(company=company, warehouse=warehouse, pos_profile=POS_PROFILE)


def get_company():
	company = frappe.db.get_value("Company", {"abbr": COMPANY_ABBR}, "name")
	if company:
		return company

	company = frappe.db.get_value("Company", {}, "name")
	if not company:
		frappe.throw("No Company exists. Run erpnext's before_tests first.")
	return company


def abbr(company):
	return frappe.db.get_value("Company", company, "abbr")


def _account(company, account_type, fallback_name=None):
	"""First non-group account of a type, e.g. the company's cash account."""
	account = frappe.db.get_value(
		"Account",
		{"company": company, "account_type": account_type, "is_group": 0},
		"name",
	)
	if account:
		return account

	if fallback_name:
		return frappe.db.get_value(
			"Account", {"company": company, "name": ["like", f"{fallback_name}%"]}, "name"
		)
	return None


def _ensure_account(company, account_type, account_name):
	"""A leaf account of `account_type`, created if the chart has only a group.

	The standard ERPNext chart ships "Bank Accounts" as a group with no leaf
	under it, so a Bank mode of payment has nothing to point at on a fresh site.
	"""
	if account := _account(company, account_type):
		return account

	parent = frappe.db.get_value(
		"Account", {"company": company, "account_type": account_type, "is_group": 1}, "name"
	)
	if not parent:
		return None

	doc = frappe.get_doc(
		{
			"doctype": "Account",
			"account_name": account_name,
			"parent_account": parent,
			"company": company,
			"account_type": account_type,
			"is_group": 0,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


# ------------------------------------------------------------------ masters --


def create_item_group():
	if frappe.db.exists("Item Group", ITEM_GROUP):
		return ITEM_GROUP

	frappe.get_doc(
		{
			"doctype": "Item Group",
			"item_group_name": ITEM_GROUP,
			"parent_item_group": "All Item Groups",
			"is_group": 0,
		}
	).insert(ignore_permissions=True)
	return ITEM_GROUP


def create_warehouse(company):
	name = f"{WAREHOUSE} - {abbr(company)}"
	if frappe.db.exists("Warehouse", name):
		return name

	frappe.get_doc(
		{
			"doctype": "Warehouse",
			"warehouse_name": WAREHOUSE,
			"company": company,
			"is_group": 0,
		}
	).insert(ignore_permissions=True)
	return name


def create_customer_group():
	if frappe.db.exists("Customer Group", CUSTOMER_GROUP):
		return CUSTOMER_GROUP

	frappe.get_doc(
		{
			"doctype": "Customer Group",
			"customer_group_name": CUSTOMER_GROUP,
			"parent_customer_group": "All Customer Groups",
			"is_group": 0,
		}
	).insert(ignore_permissions=True)
	return CUSTOMER_GROUP


def create_territory():
	if frappe.db.exists("Territory", TERRITORY):
		return TERRITORY

	frappe.get_doc(
		{
			"doctype": "Territory",
			"territory_name": TERRITORY,
			"parent_territory": "All Territories",
			"is_group": 0,
		}
	).insert(ignore_permissions=True)
	return TERRITORY


def create_customer(name, customer_group=None):
	if frappe.db.exists("Customer", name):
		return name

	frappe.get_doc(
		{
			"doctype": "Customer",
			"customer_name": name,
			"customer_type": "Individual",
			"customer_group": customer_group or CUSTOMER_GROUP,
			"territory": TERRITORY,
			"mobile_no": "9000000001",
		}
	).insert(ignore_permissions=True)
	return name


def create_mode_of_payment(name, company, account_type="Cash"):
	"""A mode of payment WITH a company-scoped default account.

	payment_entry.validate resolves paid_to from this row, so a mode without an
	account for the company is exactly the case that used to fall back to
	whichever company sorted first.
	"""
	account = _ensure_account(company, account_type, f"AntPOS {account_type}")

	if frappe.db.exists("Mode of Payment", name):
		doc = frappe.get_doc("Mode of Payment", name)
	else:
		doc = frappe.new_doc("Mode of Payment")
		doc.mode_of_payment = name
		doc.type = account_type
		doc.enabled = 1

	if account and not any(r.company == company for r in doc.get("accounts", [])):
		doc.append("accounts", {"company": company, "default_account": account})

	doc.save(ignore_permissions=True)
	return name


# -------------------------------------------------------------------- items --


def _make_item(item_code, **kwargs):
	if frappe.db.exists("Item", item_code):
		return item_code

	doc = frappe.get_doc(
		{
			"doctype": "Item",
			"item_code": item_code,
			"item_name": kwargs.get("item_name", item_code),
			"item_group": ITEM_GROUP,
			"stock_uom": "Nos",
			"is_stock_item": 1,
			"has_batch_no": kwargs.get("has_batch_no", 0),
			"has_serial_no": kwargs.get("has_serial_no", 0),
			"create_new_batch": 1 if kwargs.get("has_batch_no") else 0,
			"valuation_rate": kwargs.get("valuation_rate", 60.0),
			# Deliberately set: the scan endpoint must NOT leak these.
			"last_purchase_rate": kwargs.get("valuation_rate", 60.0),
		}
	)

	if barcode := kwargs.get("barcode"):
		doc.append("barcodes", {"barcode": barcode, "barcode_type": "EAN"})

	doc.insert(ignore_permissions=True)

	if rate := kwargs.get("rate", DEFAULT_RATE):
		create_item_price(item_code, rate)

	return item_code


def create_item_price(item_code, rate, price_list=PRICE_LIST):
	existing = frappe.db.exists("Item Price", {"item_code": item_code, "price_list": price_list})
	if existing:
		return existing

	return (
		frappe.get_doc(
			{
				"doctype": "Item Price",
				"item_code": item_code,
				"price_list": price_list,
				"price_list_rate": rate,
				"selling": 1,
			}
		)
		.insert(ignore_permissions=True)
		.name
	)


def create_items():
	_make_item(ITEM_PLAIN, barcode=BARCODE_PLAIN, item_name="AntPOS Plain Item", rate=100.0)
	_make_item(
		ITEM_BATCH,
		barcode=BARCODE_BATCH,
		item_name="AntPOS Batched Item",
		has_batch_no=1,
		rate=150.0,
	)
	_make_item(
		ITEM_SERIAL,
		barcode=BARCODE_SERIAL,
		item_name="AntPOS Serialised Item",
		has_serial_no=1,
		rate=200.0,
	)
	_make_item(
		ITEM_BATCH_SERIAL,
		barcode=BARCODE_BATCH_SERIAL,
		item_name="AntPOS Batched + Serialised Item",
		has_batch_no=1,
		has_serial_no=1,
		rate=250.0,
	)


def create_batch(batch_id, item_code, expiry_date=None):
	if frappe.db.exists("Batch", batch_id):
		return batch_id

	doc = frappe.get_doc(
		{
			"doctype": "Batch",
			"batch_id": batch_id,
			"item": item_code,
			"expiry_date": expiry_date,
		}
	)
	doc.flags.ignore_mandatory = True
	doc.insert(ignore_permissions=True)
	return batch_id


# -------------------------------------------------------------------- stock --


def _receive(company, warehouse, item_code, qty, rate=60.0, batch_no=None, serial_no=None):
	"""Material Receipt using the explicit serial/batch fields.

	v15 routes serials and batches through Serial and Batch Bundle by default;
	the POS sets use_serial_batch_fields=1, so test stock is created the same way
	to keep the two consistent.
	"""
	from erpnext.stock.doctype.stock_entry.stock_entry_utils import make_stock_entry

	# make_stock_entry is declared as **args, so use_serial_batch_fields reaches
	# the Stock Entry Detail row even though it is not a named parameter.
	return make_stock_entry(
		company=company,
		item_code=item_code,
		qty=qty,
		rate=rate,
		to_warehouse=warehouse,
		purpose="Material Receipt",
		batch_no=batch_no,
		serial_no="\n".join(serial_no) if serial_no else None,
		use_serial_batch_fields=True,
	)


def receive_stock(company, warehouse):
	"""Put known stock in the warehouse for every test item."""
	if frappe.db.exists(
		"Stock Ledger Entry",
		{"item_code": ITEM_PLAIN, "warehouse": warehouse, "is_cancelled": 0},
	):
		return  # already seeded

	_receive(company, warehouse, ITEM_PLAIN, qty=100)

	create_batch(BATCH_A, ITEM_BATCH, expiry_date=add_days(today(), 365))
	create_batch(BATCH_B, ITEM_BATCH, expiry_date=add_days(today(), 730))
	# Expired on purpose: get_batches_list must exclude it. ERPNext refuses a
	# receipt into an already-expired batch, so stock it while still valid and
	# backdate the expiry afterwards.
	create_batch(BATCH_EXPIRED, ITEM_BATCH, expiry_date=add_days(today(), 365))

	_receive(company, warehouse, ITEM_BATCH, qty=40, batch_no=BATCH_A)
	_receive(company, warehouse, ITEM_BATCH, qty=25, batch_no=BATCH_B)
	_receive(company, warehouse, ITEM_BATCH, qty=10, batch_no=BATCH_EXPIRED)
	frappe.db.set_value("Batch", BATCH_EXPIRED, "expiry_date", add_days(today(), -1))

	_receive(
		company,
		warehouse,
		ITEM_SERIAL,
		qty=len(SERIALS_PLAIN),
		serial_no=SERIALS_PLAIN,
	)

	create_batch(f"{BATCH_A}-BS", ITEM_BATCH_SERIAL, expiry_date=add_days(today(), 365))
	create_batch(f"{BATCH_B}-BS", ITEM_BATCH_SERIAL, expiry_date=add_days(today(), 730))

	_receive(
		company,
		warehouse,
		ITEM_BATCH_SERIAL,
		qty=len(SERIALS_IN_BATCH_A),
		batch_no=f"{BATCH_A}-BS",
		serial_no=SERIALS_IN_BATCH_A,
	)
	_receive(
		company,
		warehouse,
		ITEM_BATCH_SERIAL,
		qty=len(SERIALS_IN_BATCH_B),
		batch_no=f"{BATCH_B}-BS",
		serial_no=SERIALS_IN_BATCH_B,
	)


# -------------------------------------------------------------- pos profile --


def create_pos_profile(company, warehouse, name=POS_PROFILE, users=None):
	if frappe.db.exists("POS Profile", name):
		return name

	doc = frappe.get_doc(
		{
			"doctype": "POS Profile",
			"name": name,
			"company": company,
			"warehouse": warehouse,
			"currency": frappe.db.get_value("Company", company, "default_currency"),
			"selling_price_list": PRICE_LIST,
			"apply_discount_on": "Grand Total",
			"cost_center": frappe.db.get_value("Cost Center", {"company": company, "is_group": 0}, "name"),
			"write_off_account": _account(company, "Round Off", "Write Off"),
			"write_off_cost_center": frappe.db.get_value(
				"Cost Center", {"company": company, "is_group": 0}, "name"
			),
			"write_off_limit": 1,
			"custom_allow_credit": 1,
			"custom_allow_partial_payments": 1,
			"custom_allow_item_name_in_in_item_search": 1,
		}
	)

	doc.append("payments", {"mode_of_payment": MODE_CASH, "default": 1, "allow_in_returns": 1})
	doc.append("payments", {"mode_of_payment": MODE_CARD, "default": 0, "allow_in_returns": 1})
	doc.append("customer_groups", {"customer_group": CUSTOMER_GROUP})

	for user in users or [frappe.session.user]:
		doc.append("applicable_for_users", {"user": user})

	doc.flags.ignore_mandatory = True
	doc.insert(ignore_permissions=True)
	return name


# ------------------------------------------------------------------ shifts --


def create_opening_shift(company=None, pos_profile=POS_PROFILE, cashier=None, submit=True):
	"""An open Ant Opening Shift, closing any shift the cashier already has.

	Ant Opening Shift refuses to validate when the cashier already has one open,
	so tests that need a fresh shift must clear the previous one first.
	"""
	company = company or get_company()
	cashier = cashier or frappe.session.user

	close_open_shifts(cashier)

	doc = frappe.get_doc(
		{
			"doctype": "Ant Opening Shift",
			"company": company,
			"pos_profile": pos_profile,
			"cashier": cashier,
			"status": "Open",
			"period_start_date": today(),
			"posting_date": today(),
		}
	)
	doc.append("opening_balance_details", {"mode_of_payment": MODE_CASH, "opening_amount": 500})
	doc.append("opening_balance_details", {"mode_of_payment": MODE_CARD, "opening_amount": 0})

	doc.insert(ignore_permissions=True)
	if submit:
		doc.submit()
	return doc


def close_open_shifts(cashier=None):
	"""Cancel every open shift for a cashier so a new one can be created."""
	cashier = cashier or frappe.session.user

	for name in frappe.get_all(
		"Ant Opening Shift",
		filters={"cashier": cashier, "docstatus": 1, "status": "Open"},
		pluck="name",
	):
		doc = frappe.get_doc("Ant Opening Shift", name)
		doc.cancel()


# -------------------------------------------------------------------- users --


def create_pos_user(email, role, first_name=None):
	"""A user with exactly one POS role, for permission tests."""
	if not frappe.db.exists("User", email):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": first_name or email.split("@")[0],
				"send_welcome_email": 0,
				"enabled": 1,
			}
		)
		user.insert(ignore_permissions=True)
	else:
		user = frappe.get_doc("User", email)

	existing = {r.role for r in user.get("roles", [])}
	if role not in existing:
		user.append("roles", {"role": role})
		user.save(ignore_permissions=True)

	return email


# --------------------------------------------------------------- teardown ---


def teardown():
	"""Remove only what this script creates.

	Scoped deliberately: shifts are matched on the test POS Profile and items on
	the ANTPOS- prefix, so running this against a site that also holds real data
	leaves that data alone. An earlier version filtered shifts on {} and would
	have deleted every shift on the site.
	"""
	shift_filter = {"pos_profile": POS_PROFILE}

	closing = frappe.get_all("Ant Closing Shift", filters=shift_filter, fields=["name", "docstatus"])
	opening = frappe.get_all("Ant Opening Shift", filters=shift_filter, fields=["name", "docstatus"])

	# Submitted documents must be cancelled before they can be deleted.
	for doctype, rows in (("Ant Closing Shift", closing), ("Ant Opening Shift", opening)):
		for row in rows:
			if row.docstatus == 1:
				try:
					frappe.get_doc(doctype, row.name).cancel()
				except Exception as e:
					print(f"  could not cancel {doctype} {row.name}: {e}")

	targets = (
		("Ant Closing Shift", shift_filter),
		("Ant Opening Shift", shift_filter),
		("POS Profile", {"name": POS_PROFILE}),
		("Item Price", {"item_code": ["like", "ANTPOS-%"]}),
		("Item", {"item_code": ["like", "ANTPOS-%"]}),
		("Batch", {"batch_id": ["like", "ANTPOS-%"]}),
		("Customer", {"name": ["in", [CUSTOMER, SECOND_CUSTOMER]]}),
		("Mode of Payment", {"name": ["in", [MODE_CASH, MODE_CARD]]}),
		("Account", {"account_name": ["like", "AntPOS %"]}),
		("Customer Group", {"name": CUSTOMER_GROUP}),
		("Territory", {"name": TERRITORY}),
		("Item Group", {"name": ITEM_GROUP}),
	)

	for doctype, filters in targets:
		for name in frappe.get_all(doctype, filters=filters, pluck="name"):
			try:
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
			except Exception as e:
				# Stock ledger entries pin items and batches; report and move on
				# rather than leaving the caller guessing.
				print(f"  kept {doctype} {name}: {str(e).splitlines()[0][:90]}")

	frappe.db.commit()


# -------------------------------------------------------------------- cli ---


def seed():
	"""Build the whole environment and open a shift."""
	if not frappe.db.exists("Company", {}):
		sys.exit(
			"No Company on this site. Install erpnext and complete setup first:\n"
			"  bench --site <site> install-app erpnext"
		)

	env = setup_pos_environment()
	shift = create_opening_shift(company=env.company)
	frappe.db.commit()
	return env, shift


def report(env, shift):
	print()
	print("  antPOS test data ready")
	print("  " + "-" * 58)
	print(f"  Company         {env.company}")
	print(f"  Warehouse       {env.warehouse}")
	print(f"  POS Profile     {env.pos_profile}")
	print(f"  Opening Shift   {shift.name}  (cashier {shift.cashier})")
	print(f"  Customers       {CUSTOMER}, {SECOND_CUSTOMER}")
	print(f"  Payment modes   {MODE_CASH} (default), {MODE_CARD}")
	print()
	print("  Scan any of these barcodes in the POS:")
	print(f"    {BARCODE_PLAIN}   {ITEM_PLAIN:<22} plain, 100 in stock")
	print(f"    {BARCODE_BATCH}   {ITEM_BATCH:<22} batch: {BATCH_A} (40), {BATCH_B} (25)")
	print(f"    {BARCODE_SERIAL}   {ITEM_SERIAL:<22} serial x{len(SERIALS_PLAIN)}")
	print(f"    {BARCODE_BATCH_SERIAL}   {ITEM_BATCH_SERIAL:<22} batch + serial")
	print()
	print(f"  Serial numbers  {', '.join(SERIALS_PLAIN)}")
	print(f"                  {', '.join(SERIALS_IN_BATCH_A + SERIALS_IN_BATCH_B)} (batched)")
	print()
	print(f"  {BATCH_EXPIRED} is expired on purpose: it must NOT appear in the")
	print("  batch dropdown. If it does, get_batches_list has regressed.")
	print()
	print("  Open /antPOS to use it.")
	print()


def main():
	args = [a for a in sys.argv[1:] if not a.startswith("-")]
	flags = {a for a in sys.argv[1:] if a.startswith("-")}

	if not args:
		sys.exit(
			"usage: env/bin/python apps/ant_pos/test-data/seed_antpos.py <site> [--teardown]\n"
			"       run from the bench root"
		)

	site = args[0]
	if not os.path.isdir(os.path.join("sites", site)):
		sys.exit(f"No such site: sites/{site}\nRun this from the bench root.")

	# frappe resolves site config, logs and the bench path relative to cwd,
	# the same way `bench` does -- from inside sites/
	os.chdir("sites")
	frappe.init(site=site)
	frappe.connect()
	frappe.set_user("Administrator")

	try:
		if "--teardown" in flags:
			teardown()
			print(f"\n  antPOS test data removed from {site}\n")
		else:
			env, shift = seed()
			report(env, shift)
	finally:
		frappe.destroy()


if __name__ == "__main__":
	main()
