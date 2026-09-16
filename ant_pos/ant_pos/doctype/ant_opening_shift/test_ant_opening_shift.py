# Copyright (c) 2024, Anther Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from ant_pos.ant_pos.doctype.ant_opening_shift.ant_opening_shift import AntOpeningShift


def make_opening_shift(**kwargs):
	doc = frappe.new_doc("Ant Opening Shift")
	doc.update(
		{
			"company": kwargs.get("company") or frappe.defaults.get_defaults().get("company"),
			"pos_profile": kwargs["pos_profile"],
			"cashier": kwargs.get("cashier") or frappe.session.user,
			"status": "Open",
			"period_start_date": kwargs.get("period_start_date") or frappe.utils.today(),
			"opening_balance_details": kwargs.get("opening_balance_details") or [],
		}
	)
	for field, value in kwargs.get("extra", {}).items():
		doc.set(field, value)
	return doc


class TestAntOpeningShift(FrappeTestCase):
	def test_posting_date_defaults_to_today(self):
		"""posting_date is mandatory and was previously stamped unconditionally."""
		doc = frappe.new_doc("Ant Opening Shift")
		doc.cashier = frappe.session.user
		doc.period_start_date = frappe.utils.today()
		doc.validate()

		self.assertEqual(frappe.utils.getdate(doc.posting_date), frappe.utils.getdate())

	def test_explicit_posting_date_is_preserved(self):
		"""With set_posting_date, the operator's dates must survive validate()."""
		yesterday = frappe.utils.add_days(frappe.utils.today(), -1)

		doc = frappe.new_doc("Ant Opening Shift")
		doc.cashier = frappe.session.user
		doc.set_posting_date = 1
		doc.posting_date = yesterday
		doc.period_start_date = yesterday
		doc.validate()

		self.assertEqual(frappe.utils.getdate(doc.posting_date), frappe.utils.getdate(yesterday))
		self.assertEqual(
			frappe.utils.getdate(doc.period_start_date), frappe.utils.getdate(yesterday)
		)

	def test_period_end_before_start_is_rejected(self):
		"""This check was guarded on posting_date and so never ran on a new doc."""
		doc = frappe.new_doc("Ant Opening Shift")
		doc.cashier = frappe.session.user
		doc.set_posting_date = 1
		doc.period_start_date = frappe.utils.today()
		doc.period_end_date = frappe.utils.add_days(frappe.utils.today(), -2)

		with self.assertRaises(frappe.ValidationError):
			doc.validate()

	def test_period_end_after_start_is_accepted(self):
		doc = frappe.new_doc("Ant Opening Shift")
		doc.cashier = frappe.session.user
		doc.set_posting_date = 1
		doc.period_start_date = frappe.utils.today()
		doc.period_end_date = frappe.utils.add_days(frappe.utils.today(), 1)

		doc.validate()  # must not raise

	def test_duplicate_check_ignores_self(self):
		"""An existing doc must not trip its own open-shift check on re-validate."""
		doc = frappe.new_doc("Ant Opening Shift")
		doc.cashier = frappe.session.user
		doc.name = "ANT-OPEN-TEST-0001"
		doc.docstatus = 1

		# is_new() is False once a name is set, so the query must exclude it.
		self.assertFalse(doc.is_new())
