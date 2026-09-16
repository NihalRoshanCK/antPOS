# Copyright (c) 2026, Anther Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today

from ant_pos.ant_pos.api.payment_entry import get_mode_of_payment_account


class TestPosPaymentEntry(FrappeTestCase):
	"""The POS sends Payment Entries with no accounts or exchange rates."""

	def setUp(self):
		frappe.db.begin()
		row = frappe.db.sql(
			"""select mpa.parent as mode, mpa.company
			from `tabMode of Payment Account` mpa
			join `tabMode of Payment` mp on mp.name = mpa.parent
			where ifnull(mpa.default_account, '') != '' and mp.enabled = 1
			limit 1""",
			as_dict=True,
		)
		customer = frappe.db.get_value("Customer", {"disabled": 0}, "name")
		if not (row and customer):
			self.skipTest("needs a mode of payment with an account and a customer")
		self.mode, self.company, self.customer = row[0].mode, row[0].company, customer

	def tearDown(self):
		frappe.db.rollback()

	def test_accounts_and_exchange_rates_are_filled_in(self):
		# The same fields Payments > Record payment sends.
		pe = frappe.get_doc(
			{
				"doctype": "Payment Entry",
				"payment_type": "Receive",
				"posting_date": today(),
				"party_type": "Customer",
				"party": self.customer,
				"mode_of_payment": self.mode,
				"company": self.company,
				"paid_amount": 10,
				"received_amount": 10,
				"reference_no": "antpos-test",
				"reference_date": today(),
			}
		)
		pe.insert(ignore_permissions=True)

		self.assertEqual(pe.paid_to, get_mode_of_payment_account(self.mode, self.company))
		self.assertTrue(pe.paid_from)
		self.assertTrue(pe.source_exchange_rate)
		self.assertTrue(pe.target_exchange_rate)

	def test_hook_runs_before_erpnext_validation(self):
		# ERPNext works out exchange rates in its validate from paid_to, so the
		# accounts must be set before that runs.
		hooks = frappe.get_hooks("doc_events")["Payment Entry"]
		self.assertIn("ant_pos.ant_pos.api.payment_entry.validate", hooks.get("before_validate", []))
		self.assertNotIn("ant_pos.ant_pos.api.payment_entry.validate", hooks.get("validate", []))
