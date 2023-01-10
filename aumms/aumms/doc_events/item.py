import frappe
from frappe import _

@frappe.whitelist()
def validate_item(doc, method):
    """
        method used to validate item doc
        args:
            doc: object of item document
            method: validate of item
    """
    # check stock uom is a purity uom
    if doc.stock_uom:
        uom_is_a_purity_uom(doc.stock_uom)
    # check sales uom is a purity uom
    if doc.sales_uom:
        uom_is_a_purity_uom(doc.sales_uom)
    # check purchase uom is a purity uom
    if doc.purchase_uom:
        uom_is_a_purity_uom(doc.purchase_uom)

def uom_is_a_purity_uom(uom):
    """
        function to check uom is a purity uom
        args:
            uom: name of uom document
        output: a message iff uom is not a purity uom
    """
    if not frappe.db.exists('UOM', {'name': uom, 'is_purity_uom': 1}):
        frappe.throw(_('{} is not a purity uom'.format(uom)))

@frappe.whitelist()
def get_purity_uom():
    """ method to get all uoms with is purity checked"""
    return frappe.db.get_all('UOM', {'is_purity_uom': 1})

@frappe.whitelist()
def check_conversion_factor_for_uom(doc, method):
    """
        method using for checking and warning the user that the coversion factor is 0
        args:
            doc: object of item document
            method: before save of item document
    """
    for uom in doc.uoms:
        if not uom.conversion_factor:
            # alert message to user
            frappe.msgprint(
                msg = _(
                    'The conversion factor between {} and {} is zero.'.format(uom.uom, doc.stock_uom)
                    ),
                title = 'Alert'
            )

@frappe.whitelist()
def making_charge_to_item(item_group, charge_based_on, type):#set making_charge_percentage from itrm group
    percentage = ''
    if charge_based_on == 'Percentage':
        if frappe.db.exists('Item Group', {'name':item_group , 'item_type':type}):
            item_group_doc = frappe.get_last_doc('Item Group', filters = {'name':item_group , 'item_type':type})
            percentage = item_group_doc.percentage
    return percentage
