"""Server-driven forms for the POS.

The POS does not hard-code which fields its forms show. It asks for a layout
here and renders whatever comes back. A layout is stored per (DocType, type)
in "Antpos Fields Layout"; without one, the defaults below (which match the
forms the POS always had) are used.

Layout JSON, as stored:

    [                                   # sections (or tabs with "sections")
      {
        "label": "Contact",             # optional
        "columns": [                    # or [{"fields": [...]}, ...]
          ["customer_name", "mobile_no"],
          [{"fieldname": "customer_type", "default": "Individual"}]
        ]
      }
    ]

A field entry is a fieldname or an object with "fieldname" and optional
overrides: label, default, description, placeholder, reqd, read_only, hidden.
Overrides can only make a field stricter where it matters (a field required
by the DocType stays required).
"""

import json

import frappe
from frappe import _
from frappe.utils import cint

LAYOUT_DOCTYPE = "Antpos Fields Layout"

QUICK_ENTRY = "Quick Entry"
GRID_ROW = "Grid Row"

# Forms the POS renders from a layout, with the layout used when none is saved.
DEFAULT_LAYOUTS = {
	("Customer", QUICK_ENTRY): [
		{
			"columns": [
				["customer_name", {"fieldname": "customer_type", "default": "Individual"}, "mobile_no", "email_id"],
				["customer_group", "territory", "gender"],
			]
		}
	],
	("Sales Invoice Item", GRID_ROW): [
		{
			"columns": [
				[{"fieldname": "qty", "label": "Quantity"}],
				["rate"],
				[{"fieldname": "discount_percentage", "label": "Discount (%)"}],
				[{"fieldname": "discount_amount", "label": "Discount amount"}],
			]
		}
	],
}

# The POS forms an admin can design, in the order the editor lists them.
EDITABLE_FORMS = (
	{
		"doctype": "Customer",
		"type": QUICK_ENTRY,
		"parent_doctype": None,
		"title": "New customer",
		"description": "The dialog a cashier uses to add a customer.",
	},
	{
		"doctype": "Sales Invoice Item",
		"type": GRID_ROW,
		"parent_doctype": "Sales Invoice",
		"title": "Cart line details",
		"description": "The fields under a cart line when it is expanded.",
	},
)

# Doctypes the POS may create through create_from_quick_entry.
QUICK_ENTRY_DOCTYPES = {"Customer"}

# ERPNext shows these as read-only on the saved Customer, but reads them on
# insert to create the primary contact, which is what its own quick entry does.
QUICK_ENTRY_INPUTS = {("Customer", "mobile_no"), ("Customer", "email_id")}

# Field types the POS can render. Layout entries of other types are dropped.
SUPPORTED_FIELDTYPES = {
	"Data",
	"Phone",
	"Int",
	"Float",
	"Currency",
	"Percent",
	"Check",
	"Select",
	"Link",
	"Date",
	"Small Text",
	"Text",
	"Long Text",
	"Text Editor",
	"Read Only",
}

OVERRIDE_KEYS = ("label", "default", "description", "placeholder", "reqd", "read_only", "hidden")

FIELD_KEYS = (
	"fieldname",
	"label",
	"fieldtype",
	"options",
	"default",
	"description",
	"reqd",
	"read_only",
	"hidden",
	"depends_on",
	"mandatory_depends_on",
	"read_only_depends_on",
	"precision",
	"non_negative",
	"length",
)


@frappe.whitelist()
def get_form_layout(doctype: str, type: str, parent_doctype: str | None = None) -> dict:
	"""The form the POS should render for `doctype` in the given context."""
	_check_read(doctype, parent_doctype)

	sections = _resolve(doctype, type, parent_doctype)
	return {"doctype": doctype, "type": type, "sections": sections}


@frappe.whitelist(methods=["POST"])
def create_from_quick_entry(doctype: str, doc: str | dict) -> dict:
	"""Create a record from the POS quick entry form.

	Only the fields the layout shows are taken from the request, so the form
	(not the caller) decides what a cashier can set.
	"""
	if doctype not in QUICK_ENTRY_DOCTYPES:
		frappe.throw(_("Quick entry is not available for {0}").format(doctype), frappe.PermissionError)
	frappe.has_permission(doctype, "create", throw=True)

	values = frappe.parse_json(doc) if isinstance(doc, str) else (doc or {})
	fields = [f for f in _iter_fields(_resolve(doctype, QUICK_ENTRY)) if not f["read_only"]]

	data = {"doctype": doctype}
	for field in fields:
		value = values.get(field["fieldname"])
		if value in (None, "") and field.get("default") not in (None, ""):
			value = field["default"]
		if value not in (None, ""):
			data[field["fieldname"]] = value

	_apply_create_defaults(doctype, data)

	new_doc = frappe.get_doc(data)
	new_doc.insert()
	return new_doc.as_dict()


@frappe.whitelist()
def get_layout_for_editing(doctype: str, type: str, default: int = 0) -> dict:
	"""The stored layout (or the default) as editable rows for the desk editor."""
	frappe.only_for("System Manager")
	stored = None if cint(default) else frappe.db.get_value(LAYOUT_DOCTYPE, {"dt": doctype, "type": type}, "layout")
	sections = normalize_layout(stored) if stored and stored.strip() else normalize_layout(get_default_layout(doctype, type))

	meta = frappe.get_meta(doctype)
	fields = [
		{
			"fieldname": df.fieldname,
			"label": _(df.label) if df.label else df.fieldname,
			# Contact fields are inputs in quick entry (see QUICK_ENTRY_INPUTS).
			"fieldtype": "Data" if _is_quick_entry_input(doctype, type, df.fieldname) else df.fieldtype,
			"reqd": cint(df.reqd),
			"read_only": 0 if _is_quick_entry_input(doctype, type, df.fieldname) else cint(df.read_only),
			"default": df.default,
		}
		for df in meta.fields
		if df.fieldtype in SUPPORTED_FIELDTYPES
	]
	return {"sections": sections, "fields": fields, "has_default": (doctype, type) in DEFAULT_LAYOUTS}


@frappe.whitelist()
def get_editable_forms() -> list:
	"""The POS forms an admin can design, and whether each is customised."""
	frappe.only_for("System Manager")
	saved = {
		(row.dt, row.type): row.modified
		for row in frappe.get_all(LAYOUT_DOCTYPE, fields=["dt", "type", "modified"])
	}
	return [
		{
			**form,
			"title": _(form["title"]),
			"description": _(form["description"]),
			"customised": (form["doctype"], form["type"]) in saved,
			"modified": saved.get((form["doctype"], form["type"])),
		}
		for form in EDITABLE_FORMS
	]


@frappe.whitelist(methods=["POST"])
def save_form_layout(doctype: str, type: str, layout: str | list) -> dict:
	"""Store a layout from the POS editor."""
	frappe.only_for("System Manager")
	_check_editable(doctype, type)
	text = layout if isinstance(layout, str) else json.dumps(layout)

	name = frappe.db.get_value(LAYOUT_DOCTYPE, {"dt": doctype, "type": type})
	doc = frappe.get_doc(LAYOUT_DOCTYPE, name) if name else frappe.new_doc(LAYOUT_DOCTYPE)
	doc.update({"dt": doctype, "type": type, "layout": text})
	doc.save()
	return {"sections": normalize_layout(doc.layout), "modified": doc.modified}


@frappe.whitelist(methods=["POST"])
def reset_form_layout(doctype: str, type: str) -> dict:
	"""Drop the stored layout, so the POS uses the built-in one again."""
	frappe.only_for("System Manager")
	_check_editable(doctype, type)
	name = frappe.db.get_value(LAYOUT_DOCTYPE, {"dt": doctype, "type": type})
	if name:
		frappe.delete_doc(LAYOUT_DOCTYPE, name)
	return {"sections": normalize_layout(get_default_layout(doctype, type))}


@frappe.whitelist(methods=["POST"])
def preview_form_layout(doctype: str, type: str, layout: str | list, parent_doctype: str | None = None) -> dict:
	"""Resolve an unsaved layout exactly as get_form_layout would."""
	frappe.only_for("System Manager")
	_check_editable(doctype, type)
	sections = validate_layout(doctype, layout)
	return {
		"doctype": doctype,
		"type": type,
		"sections": _resolve(doctype, type, parent_doctype, sections=sections),
	}


def _check_editable(doctype, type):
	if not any(f["doctype"] == doctype and f["type"] == type for f in EDITABLE_FORMS):
		frappe.throw(_("{0} / {1} is not a POS form").format(doctype, type))


def _is_quick_entry_input(doctype, type, fieldname):
	return type == QUICK_ENTRY and (doctype, fieldname) in QUICK_ENTRY_INPUTS


def get_default_layout(doctype: str, type: str) -> list:
	return json.loads(json.dumps(DEFAULT_LAYOUTS.get((doctype, type), [])))


def normalize_layout(layout) -> list:
	"""Stored JSON (tabs, sections, column dicts or lists) to a list of
	{"label", "columns": [[entry, ...], ...]}."""
	if isinstance(layout, str):
		layout = json.loads(layout) if layout.strip() else []
	if isinstance(layout, dict):
		layout = [layout]
	if not isinstance(layout, list):
		frappe.throw(_("Layout must be a list of sections"))

	sections = []
	for block in layout:
		if not isinstance(block, dict):
			frappe.throw(_("Each section must be an object"))
		if "sections" in block:  # a tab
			sections.extend(normalize_layout(block.get("sections") or []))
			continue

		columns = []
		for column in block.get("columns") or []:
			entries = column.get("fields") if isinstance(column, dict) else column
			if not isinstance(entries, list):
				frappe.throw(_("Each column must be a list of fields"))
			columns.append(entries)
		if "fields" in block and not columns:  # a section with a flat field list
			columns.append(block["fields"])

		sections.append({"label": block.get("label") or "", "columns": columns})
	return sections


def validate_layout(doctype: str, layout) -> list:
	"""Raise if the layout names fields the DocType does not have."""
	meta = frappe.get_meta(doctype)
	sections = normalize_layout(layout)
	unknown = []
	for section in sections:
		for column in section["columns"]:
			for entry in column:
				fieldname = _entry_fieldname(entry)
				if not fieldname:
					frappe.throw(_("Every field entry needs a fieldname"))
				if not meta.get_field(fieldname):
					unknown.append(fieldname)
	if unknown:
		frappe.throw(
			_("{0} has no field(s): {1}").format(doctype, ", ".join(sorted(set(unknown)))),
			title=_("Invalid layout"),
		)
	return sections


def _resolve(doctype: str, type: str, parent_doctype: str | None = None, sections: list | None = None) -> list:
	if sections is None:
		stored = frappe.db.get_value(LAYOUT_DOCTYPE, {"dt": doctype, "type": type}, "layout")
		sections = normalize_layout(stored) if stored and stored.strip() else []
	if not any(column for section in sections for column in section["columns"]):
		sections = normalize_layout(get_default_layout(doctype, type))

	meta = frappe.get_meta(doctype)
	quick_entry = type == QUICK_ENTRY
	perms = _permlevels(doctype, parent_doctype)
	seen = set()

	resolved = []
	for section in sections:
		columns = []
		for column in section["columns"]:
			fields = []
			for entry in column:
				field = _build_field(meta, entry, quick_entry, perms)
				if field and field["fieldname"] not in seen:
					seen.add(field["fieldname"])
					fields.append(field)
			if fields:
				columns.append(fields)
		if columns:
			resolved.append({"label": section["label"], "columns": columns})

	if quick_entry:
		_append_missing_mandatory(meta, resolved, seen, perms)

	return resolved


def _build_field(meta, entry, quick_entry: bool, perms) -> dict | None:
	fieldname = _entry_fieldname(entry)
	df = meta.get_field(fieldname) if fieldname else None
	if not df or df.fieldtype not in SUPPORTED_FIELDTYPES:
		return None

	field = {key: df.get(key) for key in FIELD_KEYS}
	field["label"] = _(df.label) if df.label else fieldname
	for key in ("reqd", "read_only", "hidden", "non_negative"):
		field[key] = cint(field[key])
	if not quick_entry:
		# On an existing record (a cart line) the server fills what the DocType
		# requires (rate, item name, accounts); only a layout can ask for more.
		field["reqd"] = 0

	if (meta.name, fieldname) in QUICK_ENTRY_INPUTS and quick_entry:
		field["fieldtype"] = "Data"
		field["read_only"] = 0
	elif df.fieldtype == "Read Only":
		field["read_only"] = 1

	if isinstance(entry, dict):
		for key in OVERRIDE_KEYS:
			if key not in entry:
				continue
			if key == "reqd":
				field["reqd"] = cint(field["reqd"] or entry["reqd"])
			elif key == "read_only":
				# Can lock a field for the POS, never unlock one.
				field["read_only"] = cint(field["read_only"] or entry["read_only"])
			elif key != "hidden":
				field[key] = entry[key]

		# Hidden with a default means "always set this"; a required field
		# without a value to fall back on must stay visible.
		if "hidden" in entry:
			has_default = field.get("default") not in (None, "")
			field["hidden"] = cint(entry["hidden"]) if (has_default or not field["reqd"]) else 0

	if field["fieldtype"] == "Select":
		field["options"] = [o for o in (df.options or "").split("\n")]

	# Permission levels: read-only without write access, hidden without read.
	if df.permlevel:
		if df.permlevel not in perms["write"]:
			field["read_only"] = 1
		if df.permlevel not in perms["read"]:
			field["hidden"] = 1

	return field


def _append_missing_mandatory(meta, sections, seen, perms):
	"""A quick entry form must be submittable: add required fields the layout
	left out, unless the DocType fills them itself."""
	missing = []
	for df in meta.fields:
		if not df.reqd or df.fieldname in seen or df.default or df.read_only or df.hidden:
			continue
		if df.fieldtype not in SUPPORTED_FIELDTYPES or df.fieldname == "naming_series":
			continue
		field = _build_field(meta, df.fieldname, True, perms)
		if field:
			missing.append(field)
			seen.add(df.fieldname)

	if not missing:
		return
	if not sections:
		sections.append({"label": "", "columns": [[]]})
	sections[-1]["columns"][-1].extend(missing)


def _apply_create_defaults(doctype: str, data: dict):
	if doctype == "Customer":
		meta = frappe.get_meta("Customer")
		# India Compliance: a walk-in customer is unregistered unless told otherwise.
		if meta.get_field("gst_category") and not data.get("gst_category"):
			data["gst_category"] = "Unregistered"


def _iter_fields(sections):
	for section in sections:
		for column in section["columns"]:
			yield from column


def _entry_fieldname(entry):
	if isinstance(entry, str):
		return entry.strip()
	if isinstance(entry, dict):
		return (entry.get("fieldname") or "").strip()
	return None


def _check_read(doctype: str, parent_doctype: str | None):
	meta = frappe.get_meta(doctype)
	if meta.istable:
		if not parent_doctype or not any(
			df.options == doctype for df in frappe.get_meta(parent_doctype).get_table_fields()
		):
			frappe.throw(_("A parent DocType is required for {0}").format(doctype), frappe.PermissionError)
		frappe.has_permission(parent_doctype, "read", throw=True)
	else:
		frappe.has_permission(doctype, "read", throw=True)


def _permlevels(doctype: str, parent_doctype: str | None) -> dict:
	meta = frappe.get_meta(parent_doctype if frappe.get_meta(doctype).istable and parent_doctype else doctype)
	roles = set(frappe.get_roles())
	levels = {"read": {0}, "write": {0}}
	for perm in meta.permissions:
		if perm.role not in roles:
			continue
		if perm.get("read"):
			levels["read"].add(perm.permlevel)
		if perm.get("write"):
			levels["write"].add(perm.permlevel)
	return levels
