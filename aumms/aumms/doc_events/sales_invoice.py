import frappe
from aumms.aumms.utils import *

@frappe.whitelist()
def get_item_details(item_code, item_type, date, time, purity, stock_uom):
    ''' Method for fetching qty, making_charge_percentage, making_charge & board_rate '''
    item_details = { 'qty':0, 'making_charge_percentage':0, 'making_charge':0,  'board_rate':0  }
    if item_code:
        item_doc = frappe.get_doc('Item', item_code)
        item_details['making_charge_based_on'] = item_doc.making_charge_based_on
        item_details['qty'] = item_doc.weight_per_unit
        item_details['making_charge_percentage'] = item_doc.making_charge_percentage
        item_details['making_charge'] = item_doc.making_charge
        item_details['board_rate'] = get_board_rate(item_type, purity, stock_uom, date, time)
    return item_details

@frappe.whitelist()
def check_is_purity_item(item_type):
    ''' Method for fetching items with is_purity_item as 1 '''
    is_purity = ''
    if frappe.db.exists('Item Type', {'name': item_type, 'is_purity_item': 1}):
        is_purity = frappe.db.get_value('Item Type', {'name': item_type , 'is_purity_item': 1}, 'is_purity_item')
    return is_purity

@frappe.whitelist()
def set_customer_type (customer):
    ''' Method for setting customer type in sales invoice item'''
    if frappe.db.exists('Customer', customer, 'customer_type'):
        customer_type = frappe.db.get_value('Customer', customer, 'customer_type')
    return customer_type
