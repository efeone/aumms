import frappe
from frappe import _
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_invoice

@frappe.whitelist()
def create_purchase_invoice(doc, method=None):
    """
        method to create Purchase Invoice
        args:
            doc: object of purchase Receipt doctype
            method: on submit of purchase reciept
        output: new purchase invoice doc
    """
    # using purchase invoice creation function from purchase receipt
    make_purchase_invoice(doc.name).insert(ignore_permissions = 1)
    # message to user after creation of purchase receipt
    frappe.msgprint(_('Purchase Invoice created for the Supplier {0}'.format(doc.supplier)), alert = 1)
