import frappe
from frappe import _
from erpnext.stock.get_item_details import get_price_list_rate_for
from erpnext.accounts.doctype.pos_invoice.pos_invoice import POSInvoice

@frappe.whitelist()
def calculate_invoice_item_taxes(doc):
    """Price an in-progress cart without persisting it.

    Returns the invoice as ERPNext would compute it (taxes, totals, pricing
    rules) so the POS can show live figures.
    """
    try:
        if isinstance(doc, str):
            doc = frappe.parse_json(doc)
    except Exception as e:
        frappe.throw(_("Invalid JSON input: {0}").format(e))

    if not isinstance(doc, dict):
        frappe.throw(_("Invalid document payload"))

    # The caller controls this payload, so pin the doctype rather than letting it
    # instantiate an arbitrary controller, and keep the normal permission check.
    doc["doctype"] = "Sales Invoice"
    frappe.has_permission("Sales Invoice", "create", throw=True)

    invoice = frappe.get_doc(doc)
    invoice.set_missing_values()
    invoice.calculate_taxes_and_totals()
    if not invoice.ignore_pricing_rule:
        for item in invoice.items:
            data = get_price_list_rate_for(
                {
                    'price_list': 'Standard Selling', 
                    "customer": invoice.customer,
                    "uom":item.uom,
                    "transaction_date": invoice.posting_date,
                    "batch_no": item.batch_no,
                },
                item.item_code
            )
            item.price_list_rate=data
    return invoice.as_dict()

def before_save_sales_invoice(doc, method):
    if doc.is_pos:
        doc.__class__ = POSInvoice
        doc.validate_stock_availablility()
