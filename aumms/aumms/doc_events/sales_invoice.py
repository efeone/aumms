import frappe
from aumms.aumms.utils import *

@frappe.whitelist()
def get_item_details(item_code, item_type, date, time, purity):
    ''' Method for fetching qty, making_charge_percentage, making_charge & board_rate '''
    item_details = { 'qty':0, 'making_charge_percentage':0, 'making_charge':0,  'board_rate':0  }
    if item_code:
        item_doc = frappe.get_doc('Item', item_code)
        item_details['qty'] = item_doc.weight_per_unit
        item_details['making_charge_percentage'] = item_doc.making_charge_percentage
        item_details['making_charge'] = item_doc.making_charge
        board_rate = get_board_rate(date, time, item_type, item_doc.stock_uom, purity)
        item_details['board_rate'] = board_rate
    return item_details
