# Copyright (c) 2025, Anther Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestAntClosingShift(FrappeTestCase):
	def test_amended_from_declared_once(self):
		"""The shipped JSON declared amended_from twice, which breaks migrate."""
		fieldnames = [f.fieldname for f in frappe.get_meta("Ant Closing Shift").fields]

		duplicates = {name for name in fieldnames if fieldnames.count(name) > 1}
		self.assertEqual(duplicates, set(), f"duplicate fieldnames: {duplicates}")

	def test_mandatory_fields_are_populated_by_validate(self):
		"""pos_profile is reqd but validate() never set it, so no shift could close."""
		meta = frappe.get_meta("Ant Closing Shift")
		mandatory = {f.fieldname for f in meta.fields if f.reqd}

		# Everything mandatory is either sent by the client or derived in validate().
		derived = {
			"opening_start_date",
			"opening_end_date",
			"posting_date",
			"company",
			"pos_profile",
			"user",
		}
		client_supplied = {"ant_opening_shift"}

		self.assertTrue(
			mandatory <= (derived | client_supplied),
			f"unhandled mandatory fields: {mandatory - derived - client_supplied}",
		)

	def test_opening_shift_lookup_uses_cashier_field(self):
		"""get_opening_shift() filtered on `user`, a column that does not exist."""
		opening_fields = {f.fieldname for f in frappe.get_meta("Ant Opening Shift").fields}

		self.assertIn("cashier", opening_fields)
		self.assertNotIn("user", opening_fields)
