import frappe
@frappe.whitelist()
#Function to autoname item_group_name and item_type#
def autoname_item_group(doc,method):
	if doc.item_type:
		item_group = doc.item_group_name + '-' + doc.item_type
		doc.name = item_group



