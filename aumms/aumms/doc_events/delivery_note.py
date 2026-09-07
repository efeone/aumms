import frappe

from aumms.aumms.doctype.jewellery_invoice.jewellery_invoice import set_items_disabled


def delivery_note_on_cancel(doc, method=None):
    '''
        Method to enable the Item again when a delivery is cancelled, so a fresh Delivery
        Note can be raised against the same Sales Invoice.

        The AuMMS Item stays disabled. The piece is still sold, it just has not left yet.
    '''
    jewellery_invoice = frappe.db.get_value('Jewellery Invoice', {'delivery_note': doc.name}, 'name')
    if jewellery_invoice:
        set_items_disabled(jewellery_invoice, 0)
