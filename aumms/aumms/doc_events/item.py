import frappe
from frappe import _

@frappe.whitelist()
def validate_item(doc, method):
    """
        method used to validate item doc
        args:
            doc: object of item document
            method: validate of item
    """
    # check stock uom is a purity uom
    if doc.stock_uom:
        uom_is_a_purity_uom(doc.stock_uom)
    # check sales uom is a purity uom
    if doc.sales_uom:
        uom_is_a_purity_uom(doc.sales_uom)
    # check purchase uom is a purity uom
    if doc.purchase_uom:
        uom_is_a_purity_uom(doc.purchase_uom)

def uom_is_a_purity_uom(uom):
    """
        function to check uom is a purity uom
        args:
            uom: name of uom document
        output: a message iff uom is not a purity uom 
    """
    if not frappe.db.exists('UOM', {'name': uom, 'is_purity_uom': 1}):
        frappe.throw(_('{} is not a purity uom'.format(uom)))