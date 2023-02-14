import frappe
from frappe import _
from aumms.aumms.utils import *


@frappe.whitelist()
def set_supplier_type (supplier):
    ''' Method for setting supplier type in purchase order item'''
    if frappe.db.exists('Supplier', supplier, 'supplier_type'):
        supplier_type = frappe.db.get_value('Supplier', supplier, 'supplier_type')
    return supplier_type
