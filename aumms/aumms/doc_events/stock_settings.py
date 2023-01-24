import frappe

@frappe.whitelist()
def disable_price_list_default(doc, method=None):
    """" method to uncheck auto_insert_price_list_rate_if_missing on validate """
    if doc.auto_insert_price_list_rate_if_missing:
        doc.auto_insert_price_list_rate_if_missing = 0