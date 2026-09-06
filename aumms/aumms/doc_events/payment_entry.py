import frappe

def payment_entry_on_submit(doc, method):
    ''' Method to trigger on_submit of Payment Entry '''
    update_linked_jewellery_invoice(doc)

def payment_entry_on_cancel(doc, method):
    ''' Method to trigger on_cancel of Payment Entry '''
    update_linked_jewellery_invoice(doc)

def update_linked_jewellery_invoice(doc):
    ''' Method to recalculate the settlement of the Jewellery Invoice this payment belongs to '''
    jewellery_invoice = doc.get('jewellery_invoice') or resolve_from_references(doc)
    if not jewellery_invoice or not frappe.db.exists('Jewellery Invoice', jewellery_invoice):
        return
    if not doc.get('jewellery_invoice'):
        # Backfill so a Payment Entry raised outside the Jewellery Invoice is counted from now on
        doc.db_set('jewellery_invoice', jewellery_invoice, update_modified=False)
    frappe.get_doc('Jewellery Invoice', jewellery_invoice).update_settlement()

def resolve_from_references(doc):
    ''' Method to find the Jewellery Invoice behind the Sales Order or Sales Invoice referenced '''
    reference_fields = { 'Sales Invoice': 'sales_invoice', 'Sales Order': 'sales_order' }
    for row in doc.get('references') or []:
        reference_field = reference_fields.get(row.reference_doctype)
        if reference_field and row.reference_name:
            jewellery_invoice = frappe.db.get_value('Jewellery Invoice', { reference_field: row.reference_name })
            if jewellery_invoice:
                return jewellery_invoice
    return None
