// Copyright (c) 2025, Anther Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

// Which fields the POS shows in a form. Used today by:
//   Customer / Quick Entry         -> the POS "New customer" dialog
//   Sales Invoice Item / Grid Row  -> the details of a cart line
// "Edit fields" edits the layout as a list instead of raw JSON.

const API = "ant_pos.ant_pos.api.form_layout";
const OVERRIDES = ["label", "default", "reqd", "read_only", "hidden"];

frappe.ui.form.on("Antpos Fields Layout", {
	refresh(frm) {
		add_buttons(frm);
	},
	// On a new record the buttons appear as soon as both are picked.
	dt(frm) {
		add_buttons(frm);
	},
	type(frm) {
		add_buttons(frm);
	},
});

function add_buttons(frm) {
	frm.remove_custom_button(__("Edit fields"));
	frm.remove_custom_button(__("Start from default"));
	if (!frm.doc.dt || !frm.doc.type) {
		frm.set_intro(__("Pick a Document Type and a Type, then use Edit fields."), "blue");
		return;
	}
	frm.set_intro("");
	frm.add_custom_button(__("Edit fields"), () => open_editor(frm, 0)).addClass("btn-primary");
	frm.add_custom_button(__("Start from default"), () => open_editor(frm, 1));
}

function open_editor(frm, from_default) {
	frappe.call({
		method: `${API}.get_layout_for_editing`,
		args: { doctype: frm.doc.dt, type: frm.doc.type, default: from_default },
		callback({ message }) {
			if (from_default && !message.has_default) {
				frappe.msgprint(__("There is no built-in layout for {0} / {1}.", [frm.doc.dt, frm.doc.type]));
			}
			show_editor(frm, message);
		},
	});
}

function to_rows(sections) {
	const rows = [];
	for (const section of sections) {
		section.columns.forEach((column, c) => {
			for (const entry of column) {
				const e = typeof entry === "string" ? { fieldname: entry } : entry;
				rows.push({
					section: section.label || "",
					column: String(c + 1),
					fieldname: e.fieldname,
					label: e.label || "",
					default: e.default ?? "",
					reqd: e.reqd ? 1 : 0,
					read_only: e.read_only ? 1 : 0,
					hidden: e.hidden ? 1 : 0,
				});
			}
		});
	}
	return rows;
}

function to_sections(rows) {
	const sections = [];
	for (const row of rows) {
		if (!row.fieldname) continue;
		const label = (row.section || "").trim();
		let section = sections.find((s) => s.label === label);
		if (!section) {
			section = { label, columns: [] };
			sections.push(section);
		}
		const c = Math.max(parseInt(row.column, 10) || 1, 1) - 1;
		while (section.columns.length <= c) section.columns.push([]);

		const entry = { fieldname: row.fieldname };
		if (row.label) entry.label = row.label;
		if (row.default !== "" && row.default != null) entry.default = row.default;
		for (const key of ["reqd", "read_only", "hidden"]) if (row[key]) entry[key] = 1;
		section.columns[c].push(Object.keys(entry).length > 1 ? entry : row.fieldname);
	}
	for (const section of sections) section.columns = section.columns.filter((col) => col.length);
	return sections.filter((s) => s.columns.length);
}

function show_editor(frm, { sections, fields }) {
	const field_options = fields.map((f) => ({
		value: f.fieldname,
		label: `${f.label} (${f.fieldname})`,
	}));

	const dialog = new frappe.ui.Dialog({
		title: __("{0} / {1}: fields", [frm.doc.dt, frm.doc.type]),
		size: "extra-large",
		fields: [
			{
				fieldtype: "HTML",
				options: `<p class="text-muted small">${__(
					"Rows are shown in this order. Rows with the same section are grouped; the column number places a field side by side with others. Required fields the DocType needs are added automatically in quick entry forms."
				)}</p>`,
			},
			{
				fieldname: "rows",
				fieldtype: "Table",
				label: __("Fields"),
				cannot_add_rows: false,
				in_place_edit: true,
				data: to_rows(sections),
				fields: [
					{ fieldname: "fieldname", fieldtype: "Autocomplete", label: __("Field"), options: field_options, in_list_view: 1, reqd: 1, columns: 3 },
					{ fieldname: "section", fieldtype: "Data", label: __("Section"), in_list_view: 1, columns: 2 },
					{ fieldname: "column", fieldtype: "Select", label: __("Column"), options: "1\n2\n3\n4", default: "1", in_list_view: 1, columns: 1 },
					{ fieldname: "label", fieldtype: "Data", label: __("Label"), in_list_view: 1, columns: 2 },
					{ fieldname: "default", fieldtype: "Data", label: __("Default"), in_list_view: 1, columns: 1 },
					{ fieldname: "reqd", fieldtype: "Check", label: __("Required"), in_list_view: 1, columns: 1 },
					{ fieldname: "read_only", fieldtype: "Check", label: __("Read only"), columns: 1 },
					{ fieldname: "hidden", fieldtype: "Check", label: __("Hidden"), columns: 1 },
				],
			},
		],
		primary_action_label: __("Apply"),
		primary_action(values) {
			const layout = to_sections(values.rows || []);
			frm.set_value("layout", JSON.stringify(layout, null, 2));
			dialog.hide();
			frm.save();
		},
	});
	dialog.show();
}
