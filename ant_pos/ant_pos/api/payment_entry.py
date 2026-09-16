import frappe
from erpnext.accounts.party import get_party_account
from frappe import _


def get_mode_of_payment_account(mode_of_payment: str, company: str) -> str | None:
	"""Default account for a mode of payment, scoped to the company.

	Mode of Payment Account is a per-company child table, so an unscoped lookup
	returns whichever company happens to sort first.
	"""
	if not (mode_of_payment and company):
		return None

	return frappe.db.get_value(
		"Mode of Payment Account",
		{"parent": mode_of_payment, "company": company},
		"default_account",
	)


def validate(doc, method=None):
	"""Resolve the accounts the POS deliberately leaves blank.

	Which ledger a POS payment hits is company-specific, so the client sends the
	mode of payment and the party and lets the server decide. Every branch is
	guarded on the field being empty, so Payment Entries created anywhere else
	are untouched.
	"""
	if not doc.paid_to:
		doc.paid_to = get_mode_of_payment_account(doc.mode_of_payment, doc.company)

	if not doc.paid_from and doc.payment_type == "Receive" and doc.party_type == "Customer" and doc.party:
		doc.paid_from = get_party_account("Customer", doc.party, doc.company)

	# The original read the currency of paid_from and stored it against paid_to.
	if not doc.paid_to_account_currency and doc.paid_to:
		doc.paid_to_account_currency = frappe.db.get_value("Account", doc.paid_to, "account_currency")

	if not doc.paid_from_account_currency and doc.paid_from:
		doc.paid_from_account_currency = frappe.db.get_value("Account", doc.paid_from, "account_currency")

	# ERPNext requires a reference date whenever a reference number is present.
	if doc.reference_no and not doc.reference_date:
		doc.reference_date = doc.posting_date or frappe.utils.today()


@frappe.whitelist()
def get_payments(shift):
	"""Total received per mode of payment for one opening shift."""
	frappe.has_permission("Ant Opening Shift", "read", throw=True)

	# Query 1: Payment Entry Reference
	payment_entry = frappe.db.sql(
		"""
        SELECT
            pe.mode_of_payment,
            SUM(per.allocated_amount) AS total
        FROM `tabPayment Entry Reference` per
        JOIN `tabSales Invoice` si ON per.reference_name = si.name
        JOIN `tabPayment Entry` pe ON per.parent = pe.name
        WHERE per.reference_doctype = 'Sales Invoice'
          AND pe.docstatus = 1
          AND si.custom_ant_opening = %s
        GROUP BY pe.mode_of_payment
    """,
		(shift,),
		as_dict=True,
	)

	# Query 2: Sales Invoice Payment
	sales_payment = frappe.db.sql(
		"""
        SELECT
            p.mode_of_payment,
            SUM(p.amount) AS total
        FROM `tabSales Invoice Payment` p
        JOIN `tabSales Invoice` si ON p.parent = si.name
        WHERE si.custom_ant_opening = %s
          AND si.docstatus = 1
        GROUP BY p.mode_of_payment
    """,
		(shift,),
		as_dict=True,
	)

	# Merge and calculate totals
	result_map = {}

	for entry in payment_entry:
		mop = entry["mode_of_payment"]
		result_map[mop] = float(entry["total"] or 0)

	for payment in sales_payment:
		mop = payment["mode_of_payment"]
		result_map[mop] = result_map.get(mop, 0) + float(payment["total"] or 0)

	result_list = [{"mode_of_payment": mop, "total": total} for mop, total in result_map.items()]

	result_list.append({"mode_of_payment": "Total", "total": sum(result_map.values())})

	return result_list
