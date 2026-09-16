# Copyright (c) 2024, Anther Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import date_diff, today


class AntOpeningShift(Document):
	def validate(self):
		if not self.cashier:
			self.cashier = frappe.session.user

		# `set_posting_date` means "I will supply the dates myself".
		if not self.set_posting_date:
			self.period_start_date = today()

		if not self.posting_date:
			self.posting_date = today()

		self.validate_period()
		self.validate_no_open_shift()

	def validate_period(self):
		"""A shift cannot end before it starts."""
		if not (self.period_start_date and self.period_end_date):
			return

		# The previous check was guarded on `self.posting_date`, which is always
		# empty on a new document, so it never ran on the path that mattered.
		if date_diff(self.period_end_date, self.period_start_date) < 0:
			frappe.throw(
				_("Period End Date cannot be earlier than Period Start Date."),
				title=_("Invalid Period"),
			)

	def validate_no_open_shift(self):
		if self.get_openingshift_for_user(self.cashier):
			frappe.throw(
				_("{0} already has an open shift. Close it before opening another.").format(
					frappe.bold(self.cashier)
				),
				title=_("Shift Already Open"),
			)

	def get_openingshift_for_user(self, user):
		filters = {"cashier": user, "docstatus": 1, "status": "Open"}

		# Without this the document trips over itself on any re-validate
		# (amend, or a save after submit).
		if not self.is_new():
			filters["name"] = ["!=", self.name]

		return frappe.db.exists("Ant Opening Shift", filters)
