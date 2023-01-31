import frappe
from frappe import _

@frappe.whitelist()
def check_is_purity(doc, method):#frappe throw for purty item
    if frappe.db.exists('Item', {'name':doc.item_code }):
        is_purity = frappe.db.get_value('Item', {'name':doc.item_code }, 'is_purity_item')
        if is_purity:
            frappe.throw(_('You cannot create item price for this item {}, since it is a purity item '.format(doc.item_code) ))
