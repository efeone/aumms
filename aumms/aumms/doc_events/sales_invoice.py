import frappe

@frappe.whitelist()#function for qty, making_charge_percentage, making_charge & board_rate fetching
def fetch_qty(item,type):
    qty = ''
    charge_percentage = ''
    charge = ''
    rate = ''
    if item:
        item_doc = frappe.get_doc('Item', item)
        qty = item_doc.weight_per_unit
        charge_percentage = item_doc.making_charge_percentage
        charge = item_doc.making_charge
    if type:
        b_rate = frappe.get_last_doc('Board Rate', {'item_type':type})
        rate = b_rate.board_rate
    return (qty, charge_percentage, charge, rate)
