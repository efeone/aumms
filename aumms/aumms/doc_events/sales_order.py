import frappe
from aumms.aumms.utils import *

@frappe.whitelist()
def get_item_details(item_code, item_type, date, purity, stock_uom):
    ''' Method for fetching qty, making_charge_percentage, making_charge & board_rate '''
    item_details = { 'qty':0, 'making_charge_percentage':0, 'making_charge':0,  'board_rate':0  }
    if item_code:
        item_doc = frappe.get_doc('AuMMS Item', item_code)
        item_details['making_charge_based_on'] = item_doc.making_charge_based_on
        item_details['gold_weight'] = item_doc.gold_weight
        item_details['stone_weight'] = item_doc.stone_weight
        item_details['stone_charge'] = item_doc.stone_charge
        item_details['net_weight'] = item_doc.weight_per_unit
        item_details['making_charge_percentage'] = item_doc.making_charge_percentage
        item_details['making_charge'] = item_doc.making_charge
        item_details['board_rate'] = get_board_rate(item_type, purity, stock_uom, date)
    return item_details

@frappe.whitelist()
def set_customer_type (customer):
    ''' Method for setting customer type in sales order item'''
    if frappe.db.exists('Customer', customer, 'customer_type'):
        customer_type = frappe.db.get_value('Customer', customer, 'customer_type')
    return customer_type
