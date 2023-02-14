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


@frappe.whitelist()
def check_is_purity_item(item_type):
    ''' Method for fetching items with is_purity_item as 1 '''
    is_purity = ''
    if frappe.db.exists('Item Type', {'name': item_type, 'is_purity_item': 1}):
        is_purity = frappe.db.get_value('Item Type', {'name': item_type , 'is_purity_item': 1}, 'is_purity_item')
    return is_purity

@frappe.whitelist()
def set_supplier_type (supplier):
    ''' Method for setting supplier type in purchase receipt item'''
    if frappe.db.exists('Supplier', supplier, 'supplier_type'):
        supplier_type = frappe.db.get_value('Supplier', supplier, 'supplier_type')
    return supplier_type
