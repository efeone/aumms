import frappe
from frappe import _
from aumms.aumms.utils import *

@frappe.whitelist()
def get_item_details(old_item, item_type, date, purity, stock_uom):
    ''' Method for fetching qty, making_charge_percentage, making_charge & board_rate '''
    item_details = { 'qty':0, 'board_rate':0  }
    if old_item:
        item_doc = frappe.get_doc('Old Jewellery Item', old_item)
        item_details['qty'] = item_doc.weight_per_unit
        item_details['board_rate'] = get_board_rate(item_type, purity, stock_uom, date)
    return item_details

@frappe.whitelist()
def set_supplier_type (supplier):
    ''' Method for setting supplier type in purchase order item'''
    if frappe.db.exists('Supplier', supplier, 'supplier_type'):
        supplier_type = frappe.db.get_value('Supplier', supplier, 'supplier_type')
    return supplier_type





