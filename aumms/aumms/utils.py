import frappe
from frappe.utils import *

@frappe.whitelist()
def get_board_rate(date, time, item_type, uom, purity=None):
    ''' Method to get Board Rate '''
    board_rate = 0
    if purity:
        filters = { 'docstatus': '1', 'item_type': item_type, 'date':getdate(date), 'time': [ '<=', time ], 'purity': purity }
    else:
        filters = { 'docstatus': '1', 'item_type': item_type, 'date':getdate(date), 'time': [ '<=', time ] }
    if frappe.db.get_all('Board Rate', filters=filters):
        board_rate_doc = frappe.get_last_doc('Board Rate', filters=filters)
        board_rate = board_rate_doc.board_rate
    return board_rate
