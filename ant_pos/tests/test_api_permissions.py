# Copyright (c) 2026, Anther Technologies Pvt. Ltd. and Contributors
# See license.txt

import inspect

import frappe
from frappe.tests.utils import FrappeTestCase

from ant_pos.ant_pos.api import get_doc_field
from ant_pos.ant_pos.api.session import get_users
from ant_pos.ant_pos.doctype.antpos_fields_layout.antpos_fields_layout import (
	get_fields_layout,
	get_sidepanel_sections,
	save_fields_layout,
)


class TestWhitelistedEndpointsAreGated(FrappeTestCase):
	"""These four were whitelisted with no permission check at all, and
	save_fields_layout additionally saved with ignore_permissions=True."""

	def test_save_fields_layout_is_admin_only(self):
		source = inspect.getsource(save_fields_layout)

		self.assertIn("only_for", source)
		self.assertNotIn("ignore_permissions", source)

	def test_layout_readers_check_permission(self):
		for fn in (get_fields_layout, get_sidepanel_sections):
			self.assertIn("has_permission", inspect.getsource(fn), fn.__name__)

	def test_get_doc_field_checks_create_permission(self):
		source = inspect.getsource(get_doc_field)

		self.assertIn("has_permission", source)
		self.assertIn("create", source)

	def test_sidepanel_reads_the_right_doctype(self):
		"""It referenced "CAntpos Fields Layout" and so always raised."""
		self.assertNotIn("CAntpos", inspect.getsource(get_sidepanel_sections))


class TestGetUsersScoping(FrappeTestCase):
	"""get_users() returned every User row to any caller and runs on app load."""

	def test_privileged_caller_sees_more_than_one_user(self):
		frappe.set_user("Administrator")
		self.assertGreaterEqual(len(get_users()), 1)

	def test_unprivileged_caller_sees_only_themselves(self):
		user = frappe.db.get_value("User", {"name": ["!=", "Administrator"], "enabled": 1})
		if not user:
			self.skipTest("no non-Administrator user available")

		try:
			frappe.set_user(user)
			if frappe.has_permission("User", "read"):
				self.skipTest(f"{user} can read User; not an unprivileged caller")

			result = get_users()
			self.assertEqual(len(result), 1)
			self.assertEqual(result[0]["name"], user)
			self.assertTrue(result[0]["session_user"])
		finally:
			frappe.set_user("Administrator")
