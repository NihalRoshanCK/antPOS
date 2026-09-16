// Copyright (c) 2025, Anther Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

// Drag-and-drop builder for the fields the POS shows in a form. Used by:
//   Customer / Quick Entry         -> the POS "New customer" dialog
//   Sales Invoice Item / Grid Row  -> the details of a cart line
//
// The builder keeps the layout in memory and writes it to the `layout` field
// (JSON) on every change; Save stores it. Drag and drop uses SortableJS, which
// the desk already loads as window.Sortable.

const API = "ant_pos.ant_pos.api.form_layout";
const MAX_COLUMNS = 4;

frappe.ui.form.on("Antpos Fields Layout", {
	refresh(frm) {
		render_builder(frm);
	},
	dt(frm) {
		frm.set_value("layout", "");
		render_builder(frm);
	},
	type(frm) {
		render_builder(frm);
	},
	layout(frm) {
		// Edited by hand in the JSON box: redraw from it.
		if (frm._alb && !frm._alb.writing) render_builder(frm);
	},
});

function render_builder(frm) {
	const wrapper = frm.get_field("layout_builder")?.$wrapper;
	if (!wrapper) return;
	if (frm._alb?.builder) frm._alb.builder.destroy();

	if (!frm.doc.dt || !frm.doc.type) {
		wrapper.html(
			`<div class="alb-empty text-muted">${__(
				"Pick a Document Type and a Type to design the form."
			)}</div>`
		);
		frm._alb = null;
		return;
	}

	wrapper.html(`<div class="alb-loading text-muted">${__("Loading fields…")}</div>`);
	frappe.call({
		method: `${API}.get_layout_for_editing`,
		args: { doctype: frm.doc.dt, type: frm.doc.type, default: 0 },
		callback({ message }) {
			const stored = parse_layout(frm.doc.layout);
			// A new layout starts from the built-in one, so the admin edits
			// what the POS shows today instead of a blank page.
			const sections = stored ?? message.sections;
			const builder = new LayoutBuilder(wrapper, {
				doctype: frm.doc.dt,
				type: frm.doc.type,
				fields: message.fields,
				sections,
				has_default: message.has_default,
				on_change: (layout) => write_layout(frm, layout),
				load_default: () => load_default(frm),
			});
			frm._alb = { builder, writing: false };
			if (stored === null && sections.length) write_layout(frm, builder.to_layout());
		},
	});
}

function load_default(frm) {
	frappe.call({
		method: `${API}.get_layout_for_editing`,
		args: { doctype: frm.doc.dt, type: frm.doc.type, default: 1 },
		callback({ message }) {
			if (!message.has_default) {
				frappe.show_alert({
					message: __("There is no built-in layout for {0} / {1}.", [frm.doc.dt, frm.doc.type]),
					indicator: "orange",
				});
				return;
			}
			frm._alb.builder.set_sections(message.sections);
		},
	});
}

function write_layout(frm, layout) {
	const json = layout.length ? JSON.stringify(layout, null, 2) : "";
	if ((frm.doc.layout || "") === json) return;
	frm._alb && (frm._alb.writing = true);
	frm.set_value("layout", json).then(() => frm._alb && (frm._alb.writing = false));
}

// Stored JSON to [{label, columns: [[entry]]}], or null when there is none.
function parse_layout(text) {
	if (!text || !text.trim()) return null;
	let data;
	try {
		data = JSON.parse(text);
	} catch (e) {
		return null;
	}
	const sections = [];
	const walk = (blocks) => {
		for (const block of Array.isArray(blocks) ? blocks : [blocks]) {
			if (!block || typeof block !== "object") continue;
			if (block.sections) {
				walk(block.sections);
				continue;
			}
			let columns = (block.columns || []).map((c) => (Array.isArray(c) ? c : c.fields || []));
			if (!columns.length && block.fields) columns = [block.fields];
			sections.push({ label: block.label || "", columns });
		}
	};
	walk(data);
	return sections;
}

class LayoutBuilder {
	constructor(wrapper, opts) {
		this.wrapper = wrapper;
		this.opts = opts;
		this.meta = Object.fromEntries(opts.fields.map((f) => [f.fieldname, f]));
		this.sortables = [];
		this.search = "";
		this.set_sections(opts.sections, { silent: true });
	}

	// ---- state ---------------------------------------------------------

	set_sections(sections, { silent = false } = {}) {
		// Overrides per field; each field appears at most once.
		this.overrides = {};
		const seen = new Set();
		this.sections = (sections || []).map((section) => ({
			label: section.label || "",
			columns: (section.columns || []).map((column) =>
				column
					.map((entry) => {
						const e = typeof entry === "string" ? { fieldname: entry } : { ...entry };
						if (!e.fieldname || !this.meta[e.fieldname] || seen.has(e.fieldname)) return null;
						seen.add(e.fieldname);
						const { fieldname, ...rest } = e;
						if (Object.keys(rest).length) this.overrides[fieldname] = rest;
						return fieldname;
					})
					.filter(Boolean)
			),
		}));
		for (const section of this.sections) if (!section.columns.length) section.columns.push([]);
		this.render();
		if (!silent) this.changed();
	}

	to_layout() {
		return this.sections
			.map((section) => ({
				label: section.label,
				columns: section.columns.map((column) =>
					column.map((fieldname) => {
						const o = this.overrides[fieldname];
						return o && Object.keys(o).length ? { fieldname, ...o } : fieldname;
					})
				),
			}))
			.filter((section) => section.columns.some((c) => c.length) || section.label);
	}

	used() {
		return new Set(this.sections.flatMap((s) => s.columns.flat()));
	}

	changed() {
		this.opts.on_change(this.to_layout());
	}

	// Read the order back from the DOM after a drag, then redraw.
	sync_from_dom() {
		const sections = [];
		this.$canvas.find(".alb-section").each((_, sec) => {
			const index = Number(sec.dataset.index);
			const columns = [];
			$(sec)
				.find(".alb-column-body")
				.each((_, col) => {
					columns.push(
						$(col)
							.find(".alb-field")
							.map((_, f) => f.dataset.fieldname)
							.get()
					);
				});
			sections.push({ label: this.sections[index]?.label || "", columns });
		});
		this.sections = sections;
		this.render();
		this.changed();
	}

	// ---- rendering -----------------------------------------------------

	destroy() {
		this.sortables.forEach((s) => s.destroy());
		this.sortables = [];
		this.palette_sortable?.destroy();
		this.palette_sortable = null;
	}

	render() {
		this.destroy();
		ensure_styles();
		const { doctype, type } = this.opts;
		this.wrapper.html(`
			<div class="alb">
				<div class="alb-toolbar">
					<div class="alb-title">
						<div class="alb-heading">${__("Form layout")}</div>
						<div class="text-muted small">${__(
							"Drag fields from the list into a column. Drag cards to reorder or move them; drag a section by its handle. Click a card for its settings."
						)}</div>
					</div>
					<div class="alb-actions">
						<button class="btn btn-default btn-xs" data-action="add-section">${frappe.utils.icon("add", "xs")} ${__("Section")}</button>
						<button class="btn btn-default btn-xs" data-action="default">${__("Start from default")}</button>
						<button class="btn btn-default btn-xs" data-action="clear">${__("Clear")}</button>
					</div>
				</div>
				<div class="alb-body">
					<aside class="alb-palette">
						<div class="alb-palette-head">
							<div class="alb-subheading">${__("Fields of {0}", [__(doctype)])}</div>
							<input type="search" class="form-control input-xs alb-search" placeholder="${__("Search fields")}" value="${frappe.utils.escape_html(this.search)}">
						</div>
						<div class="alb-palette-list"></div>
					</aside>
					<div class="alb-canvas"></div>
				</div>
				<div class="alb-foot text-muted small">${this.footnote(type)}</div>
			</div>
		`);
		this.$root = this.wrapper.find(".alb");
		this.$canvas = this.wrapper.find(".alb-canvas");
		this.render_palette();
		this.render_canvas();
		this.bind();
	}

	footnote(type) {
		if (type === "Quick Entry") {
			return __("Fields the document requires are added to the form automatically if you leave them out. Save to apply; open POS tabs pick it up when the cashier returns to them.");
		}
		return __("Save to apply; open POS tabs pick it up when the cashier returns to them.");
	}

	render_palette() {
		const used = this.used();
		const q = this.search.trim().toLowerCase();
		const available = this.opts.fields.filter(
			(f) =>
				!used.has(f.fieldname) &&
				(!q || f.label.toLowerCase().includes(q) || f.fieldname.includes(q))
		);
		const list = this.wrapper.find(".alb-palette-list");
		list.html(
			available.length
				? available.map((f) => this.palette_item(f)).join("")
				: `<div class="text-muted small alb-palette-empty">${
						q ? __("No fields match.") : __("Every field is on the form.")
				  }</div>`
		);
		this.palette_sortable?.destroy();
		this.palette_sortable = Sortable.create(list[0], {
				group: { name: "alb-fields", pull: "clone", put: false },
				sort: false,
				animation: 150,
				onEnd: (evt) => {
					// Dropped on the canvas: the clone stays there; redraw from DOM.
					if (evt.to !== list[0]) this.sync_from_dom();
				},
			});
	}

	palette_item(f) {
		return `<div class="alb-field alb-field-palette" data-fieldname="${f.fieldname}" title="${f.fieldname}">
			<span class="alb-grip">${frappe.utils.icon("drag", "xs")}</span>
			<span class="alb-field-text">
				<span class="alb-field-label">${frappe.utils.escape_html(__(f.label))}${f.reqd ? ' <span class="text-danger">*</span>' : ""}</span>
				<span class="alb-field-meta">${f.fieldtype}</span>
			</span>
		</div>`;
	}

	render_canvas() {
		if (!this.sections.length) {
			this.$canvas.html(`<div class="alb-canvas-empty">
				<p>${__("No sections yet.")}</p>
				<button class="btn btn-primary btn-sm" data-action="add-section">${__("Add a section")}</button>
				${this.opts.has_default ? `<button class="btn btn-default btn-sm" data-action="default">${__("Start from default")}</button>` : ""}
			</div>`);
			return;
		}

		this.$canvas.html(
			`<div class="alb-sections">${this.sections.map((s, i) => this.section_html(s, i)).join("")}</div>`
		);

		this.sortables.push(
			Sortable.create(this.$canvas.find(".alb-sections")[0], {
				handle: ".alb-section-grip",
				animation: 150,
				onEnd: () => this.sync_from_dom(),
			})
		);
		this.$canvas.find(".alb-column-body").each((_, el) => {
			this.sortables.push(
				Sortable.create(el, {
					group: { name: "alb-fields", pull: true, put: true },
					animation: 150,
					filter: ".alb-field-remove",
					preventOnFilter: false,
					ghostClass: "alb-ghost",
					onEnd: () => this.sync_from_dom(),
					onAdd: () => this.sync_from_dom(),
				})
			);
		});
	}

	section_html(section, index) {
		const cols = section.columns.length;
		return `<div class="alb-section" data-index="${index}">
			<div class="alb-section-head">
				<span class="alb-section-grip" title="${__("Drag to reorder")}">${frappe.utils.icon("drag", "sm")}</span>
				<input class="form-control input-xs alb-section-label" data-index="${index}"
					placeholder="${__("Section title (optional)")}" value="${frappe.utils.escape_html(section.label)}">
				<div class="alb-section-actions">
					<button class="btn btn-default btn-xs" data-action="add-column" data-index="${index}" ${cols >= MAX_COLUMNS ? "disabled" : ""}
						title="${__("Add a column")}">${frappe.utils.icon("add", "xs")} ${__("Column")}</button>
					<button class="btn btn-default btn-xs" data-action="remove-section" data-index="${index}" title="${__("Remove section")}">${frappe.utils.icon("delete", "xs")}</button>
				</div>
			</div>
			<div class="alb-columns" style="--alb-cols:${cols}">
				${section.columns.map((column, c) => this.column_html(column, index, c, cols)).join("")}
			</div>
		</div>`;
	}

	column_html(column, s, c, cols) {
		return `<div class="alb-column">
			<div class="alb-column-head">
				<span>${__("Column {0}", [c + 1])}</span>
				${cols > 1 ? `<button class="btn btn-link btn-xs alb-link" data-action="remove-column" data-index="${s}" data-column="${c}">${__("Remove")}</button>` : ""}
			</div>
			<div class="alb-column-body ${column.length ? "" : "alb-column-empty"}" data-empty="${__("Drop fields here")}">${column
				.map((fieldname) => this.card_html(fieldname))
				.join("")}</div>
		</div>`;
	}

	card_html(fieldname) {
		const f = this.meta[fieldname];
		const o = this.overrides[fieldname] || {};
		const badges = [];
		if (o.reqd || f.reqd) badges.push(`<span class="alb-badge alb-badge-red">${__("Required")}</span>`);
		if (o.read_only || f.read_only) badges.push(`<span class="alb-badge">${__("Read only")}</span>`);
		if (o.hidden) badges.push(`<span class="alb-badge alb-badge-orange">${__("Hidden")}</span>`);
		if (o.default !== undefined && o.default !== "")
			badges.push(`<span class="alb-badge alb-badge-blue">= ${frappe.utils.escape_html(String(o.default))}</span>`);
		const label = o.label || __(f.label);
		return `<div class="alb-field alb-card ${o.hidden ? "alb-card-hidden" : ""}" data-fieldname="${fieldname}" tabindex="0"
				role="button" aria-label="${frappe.utils.escape_html(label)}: ${__("settings")}">
			<span class="alb-grip">${frappe.utils.icon("drag", "xs")}</span>
			<span class="alb-field-text">
				<span class="alb-field-label">${frappe.utils.escape_html(label)}</span>
				<span class="alb-field-meta">${fieldname} · ${f.fieldtype}</span>
				${badges.length ? `<span class="alb-badges">${badges.join("")}</span>` : ""}
			</span>
			<button class="btn btn-link btn-xs alb-field-remove" data-action="remove-field" data-fieldname="${fieldname}"
				title="${__("Remove from form")}" aria-label="${__("Remove {0}", [label])}">${frappe.utils.icon("close", "xs")}</button>
		</div>`;
	}

	// ---- interaction ---------------------------------------------------

	bind() {
		const root = this.$root;

		root.on("click", "[data-action]", (e) => {
			e.preventDefault();
			e.stopPropagation();
			const el = e.currentTarget;
			const index = Number(el.dataset.index);
			switch (el.dataset.action) {
				case "add-section":
					this.sections.push({ label: "", columns: [[]] });
					break;
				case "remove-section":
					this.sections.splice(index, 1);
					break;
				case "add-column":
					if (this.sections[index].columns.length < MAX_COLUMNS) this.sections[index].columns.push([]);
					break;
				case "remove-column": {
					const cols = this.sections[index].columns;
					const [removed] = cols.splice(Number(el.dataset.column), 1);
					// Keep its fields: move them to the previous column.
					cols[Math.max(Number(el.dataset.column) - 1, 0)].push(...removed);
					break;
				}
				case "remove-field":
					for (const s of this.sections) s.columns = s.columns.map((c) => c.filter((f) => f !== el.dataset.fieldname));
					delete this.overrides[el.dataset.fieldname];
					break;
				case "default":
					this.opts.load_default();
					return;
				case "clear":
					frappe.confirm(__("Remove every field from this form?"), () => this.set_sections([]));
					return;
				default:
					return;
			}
			this.render();
			this.changed();
		});

		root.on("click keydown", ".alb-card", (e) => {
			if (e.type === "keydown" && e.key !== "Enter" && e.key !== " ") return;
			if ($(e.target).closest("[data-action]").length) return;
			e.preventDefault();
			this.edit_field(e.currentTarget.dataset.fieldname);
		});

		root.on("change", ".alb-section-label", (e) => {
			this.sections[Number(e.currentTarget.dataset.index)].label = e.currentTarget.value.trim();
			this.changed();
		});

		root.on(
			"input",
			".alb-search",
			frappe.utils.debounce((e) => {
				this.search = e.target.value;
				this.render_palette();
			}, 150)
		);
	}

	edit_field(fieldname) {
		const f = this.meta[fieldname];
		const o = this.overrides[fieldname] || {};
		const dialog = new frappe.ui.Dialog({
			title: __("{0} ({1})", [__(f.label), fieldname]),
			fields: [
				{ fieldname: "label", fieldtype: "Data", label: __("Label"), default: o.label || "", description: __("Leave empty to use “{0}”.", [__(f.label)]) },
				{ fieldname: "default", fieldtype: "Data", label: __("Default value"), default: o.default ?? "", description: f.default ? __("DocType default: {0}", [f.default]) : "" },
				{ fieldtype: "Column Break" },
				{ fieldname: "reqd", fieldtype: "Check", label: __("Required"), default: o.reqd || f.reqd ? 1 : 0, read_only: f.reqd, description: f.reqd ? __("Always required by the DocType.") : "" },
				{ fieldname: "read_only", fieldtype: "Check", label: __("Read only"), default: o.read_only || f.read_only ? 1 : 0, read_only: f.read_only },
				{ fieldname: "hidden", fieldtype: "Check", label: __("Hidden"), default: o.hidden ? 1 : 0, description: __("Hidden fields still apply their default value.") },
			],
			primary_action_label: __("Apply"),
			primary_action: (v) => {
				const next = {};
				if (v.label && v.label !== __(f.label)) next.label = v.label;
				if (v.default !== "" && v.default != null) next.default = v.default;
				if (v.reqd && !f.reqd) next.reqd = 1;
				if (v.read_only && !f.read_only) next.read_only = 1;
				if (v.hidden) next.hidden = 1;
				if (Object.keys(next).length) this.overrides[fieldname] = next;
				else delete this.overrides[fieldname];
				dialog.hide();
				this.render();
				this.changed();
			},
		});
		dialog.show();
	}
}

function ensure_styles() {
	if (document.getElementById("alb-styles")) return;
	const style = document.createElement("style");
	style.id = "alb-styles";
	style.textContent = `
		.alb { border: 1px solid var(--border-color); border-radius: var(--border-radius-md); background: var(--card-bg); }
		.alb-toolbar { display: flex; flex-wrap: wrap; gap: 12px; justify-content: space-between; align-items: flex-start; padding: 12px 14px; border-bottom: 1px solid var(--border-color); }
		.alb-heading { font-weight: 600; color: var(--heading-color); }
		.alb-subheading { font-size: var(--text-sm); font-weight: 600; color: var(--heading-color); margin-bottom: 6px; }
		.alb-actions { display: flex; gap: 6px; flex-wrap: wrap; }
		.alb-body { display: grid; grid-template-columns: 240px 1fr; min-height: 360px; }
		@media (max-width: 767px) { .alb-body { grid-template-columns: 1fr; } }
		.alb-palette { border-right: 1px solid var(--border-color); background: var(--subtle-fg); display: flex; flex-direction: column; min-height: 0; }
		.alb-palette-head { padding: 10px; border-bottom: 1px solid var(--border-color); }
		.alb-palette-list { padding: 8px; overflow-y: auto; max-height: 520px; display: flex; flex-direction: column; gap: 4px; }
		.alb-palette-empty { padding: 8px; }
		.alb-canvas { padding: 12px; overflow-x: auto; }
		.alb-canvas-empty { text-align: center; padding: 48px 12px; color: var(--text-muted); }
		.alb-canvas-empty .btn { margin: 0 4px; }
		.alb-sections { display: flex; flex-direction: column; gap: 12px; }
		.alb-section { border: 1px solid var(--border-color); border-radius: var(--border-radius-md); background: var(--card-bg); }
		.alb-section-head { display: flex; align-items: center; gap: 8px; padding: 8px 10px; border-bottom: 1px solid var(--border-color); }
		.alb-section-grip { cursor: grab; color: var(--text-muted); display: inline-flex; }
		.alb-section-label { max-width: 280px; }
		.alb-section-actions { margin-left: auto; display: flex; gap: 6px; }
		.alb-columns { display: grid; grid-template-columns: repeat(var(--alb-cols), minmax(160px, 1fr)); gap: 10px; padding: 10px; }
		.alb-column { background: var(--subtle-fg); border-radius: var(--border-radius); display: flex; flex-direction: column; min-width: 0; }
		.alb-column-head { display: flex; justify-content: space-between; align-items: center; padding: 6px 8px 0; font-size: var(--text-xs); color: var(--text-muted); }
		.alb-link { padding: 0; color: var(--text-muted); }
		.alb-column-body { min-height: 64px; padding: 8px; display: flex; flex-direction: column; gap: 6px; flex: 1; border-radius: var(--border-radius); }
		.alb-column-empty::after { content: attr(data-empty); display: grid; place-items: center; min-height: 48px; border: 1px dashed var(--border-color); border-radius: var(--border-radius); color: var(--text-light); font-size: var(--text-xs); }
		.alb-column-empty:has(.alb-field)::after { display: none; }
		.alb-field { display: flex; align-items: flex-start; gap: 6px; padding: 6px 8px; border: 1px solid var(--border-color); border-radius: var(--border-radius); background: var(--card-bg); cursor: grab; user-select: none; }
		.alb-field:hover { border-color: var(--gray-400); box-shadow: var(--shadow-xs); }
		.alb-card:focus-visible { outline: 2px solid var(--primary); outline-offset: 1px; }
		.alb-card-hidden { opacity: .6; border-style: dashed; }
		.alb-grip { color: var(--text-light); display: inline-flex; padding-top: 2px; }
		.alb-field-text { display: flex; flex-direction: column; min-width: 0; flex: 1; }
		.alb-field-label { font-size: var(--text-sm); color: var(--text-color); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
		.alb-field-meta { font-size: var(--text-xs); color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
		.alb-badges { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; }
		.alb-badge { font-size: 10px; line-height: 16px; padding: 0 5px; border-radius: 4px; background: var(--bg-gray); color: var(--text-muted); }
		.alb-badge-red { background: var(--bg-red); color: var(--text-on-red); }
		.alb-badge-orange { background: var(--bg-orange); color: var(--text-on-orange); }
		.alb-badge-blue { background: var(--bg-blue); color: var(--text-on-blue); }
		.alb-field-remove { padding: 0 2px; color: var(--text-muted); opacity: 0; }
		.alb-card:hover .alb-field-remove, .alb-card:focus-within .alb-field-remove { opacity: 1; }
		.alb-ghost { opacity: .4; border-style: dashed; }
		.alb-foot { padding: 8px 14px; border-top: 1px solid var(--border-color); }
		.alb-empty, .alb-loading { padding: 24px; text-align: center; border: 1px dashed var(--border-color); border-radius: var(--border-radius-md); }
	`;
	document.head.appendChild(style);
}
