import frappe
from frappe import _
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_invoice

def purchase_receipt_on_submit(doc, method):
    ''' Method to trigger Purchase Receipt on_submit '''
    if doc.create_invoice_on_submit:
        create_purchase_invoice(doc)

@frappe.whitelist()
def create_purchase_invoice(doc):
    """
        method to create Purchase Invoice
        args:
            doc: object of purchase Receipt doctype
            method: on submit of purchase reciept
        output: new purchase invoice doc
    """
    # using purchase invoice creation function from purchase receipt
    purchase_invoice = make_purchase_invoice(doc.name).insert(ignore_permissions = 1)
    # message to user after creation of purchase receipt
    frappe.msgprint(_('Purchase Invoice created for the Supplier {0}'.format(doc.supplier)), indicator="green", alert = 1)
    if purchase_invoice:
        if purchase_invoice.docstatus == 0:
            purchase_invoice.submit()
        set_purchase_invoice_link_to_jewellery_invoice(doc.name, purchase_invoice.name)
    return purchase_invoice


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

def set_purchase_invoice_link_to_jewellery_invoice(purchase_receipt, purchase_invoice):
    if frappe.db.exists('Jewellery Invoice', { 'purchase_receipt':purchase_receipt }):
        invoice_id = frappe.db.get_value('Jewellery Invoice', { 'purchase_receipt':purchase_receipt })
        frappe.db.set_value('Jewellery Invoice', invoice_id, 'purchase_invoice', purchase_invoice)
        frappe.db.commit()
