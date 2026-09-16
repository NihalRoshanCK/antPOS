import frappe
from frappe import _
from frappe.translate import get_all_translations


def user_has_posprofile(user=None):
	"""Whether antPOS appears for this user on /apps (add_to_apps_screen).

	Cashiers see it when they are listed on an enabled POS Profile. System
	Managers always see it, since they are the ones who set the profiles up.
	"""
	user = user or frappe.session.user
	if user == "Guest":
		return False
	if "System Manager" in frappe.get_roles(user):
		return True

	profile_user = frappe.qb.DocType("POS Profile User")
	profile = frappe.qb.DocType("POS Profile")
	match = (
		frappe.qb.from_(profile_user)
		.join(profile)
		.on(profile.name == profile_user.parent)
		.select(profile_user.name)
		.where(profile_user.user == user)
		.where(profile_user.parenttype == "POS Profile")
		.where(profile.disabled == 0)
		.limit(1)
		.run()
	)
	return bool(match)


def posprofile_user_query_conditions(user=None):
	"""
	Returns SQL condition to restrict POS Profiles list to those
	where the given user exists in the 'Applicable for Users' child table.
	System Managers and Administrators get access to all POS Profiles.
	"""
	if not user:
		user = frappe.session.user

	if user == "Guest":
		return "FALSE"

	roles = frappe.get_roles(user)
	if "System Manager" in roles or "Administrator" in roles:
		return "1=1"  # full access

	return f"""
        name IN (
            SELECT parent FROM `tabPOS Profile User`
            WHERE user = {frappe.db.escape(user)}
        )
    """


@frappe.whitelist()
def get_user_permissions():
	user = frappe.session.user
	permissions = {}
	user_roles = frappe.get_roles(user)

	def check_perm(doctype, permtype):
		"""Is `permtype` owner-restricted for this user?

		Only if EVERY role that grants it is owner-restricted. Taking the first
		row meant a user holding both an unrestricted and a restricted role got
		an answer that depended on row ordering.
		"""
		# Custom DocPerm overrides the shipped DocPerm set entirely.
		perms = frappe.get_all(
			"Custom DocPerm",
			filters={"parent": doctype, "role": ["in", user_roles], permtype: 1},
			fields=["if_owner"],
		) or frappe.get_all(
			"DocPerm",
			filters={"parent": doctype, "role": ["in", user_roles], permtype: 1},
			fields=["if_owner"],
		)

		if not perms:
			return False

		return all(p["if_owner"] == 1 for p in perms)

	for doctype in ["Sales Invoice", "Payment Entry", "Sales Order"]:
		submit_owner_restricted = check_perm(doctype, "submit")

		can_submit_global = frappe.has_permission(doctype, doc=None, ptype="submit", user=user)
		can_create_global = frappe.has_permission(doctype, doc=None, ptype="create", user=user)
		can_print_global = frappe.has_permission(doctype, doc=None, ptype="print", user=user)

		# If submit is owner restricted, check if user owns any docs
		has_own_docs = False
		if submit_owner_restricted:
			has_own_docs = frappe.db.exists({"doctype": doctype, "owner": user, "docstatus": 0}) is not None

		can_submit = can_submit_global or (submit_owner_restricted and has_own_docs)

		permissions[doctype.lower().replace(" ", "_")] = {
			"can_submit": can_submit,
			"can_submit_owner_restricted": submit_owner_restricted,
			"has_own_docs": has_own_docs,
			"can_create": can_create_global,
			"can_print": can_print_global,
		}

	# Form layouts decide what every cashier sees (api/form_layout.py).
	permissions["can_manage_layouts"] = "System Manager" in user_roles
	# Brand settings and other site-wide options.
	permissions["is_system_manager"] = "System Manager" in user_roles

	return permissions


@frappe.whitelist(allow_guest=True)
def get_translations():
	if frappe.session.user != "Guest":
		language = frappe.db.get_value("User", frappe.session.user, "language")
	else:
		language = frappe.db.get_single_value("System Settings", "language")

	return get_all_translations(language)


@frappe.whitelist()
def get_doc_field():
	"""Return a blank document (with defaults applied) for the given doctype."""
	doctype = frappe.form_dict.get("doctype")

	if not doctype:
		frappe.throw(_("Missing 'doctype' parameter"))

	# Returns server-side defaults, so require the same permission as actually
	# creating the document.
	frappe.has_permission(doctype, "create", throw=True)

	try:
		return frappe.new_doc(doctype).as_dict()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "get_doc_field error")
		frappe.throw(_("Unable to create doc for {0}").format(doctype))
