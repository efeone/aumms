# Copyright (c) 2024, efeone and contributors
# # For license information, please see license.txt
import frappe
from frappe.model.document import Document

class PurchaseRequest(Document):
	pass

@frappe.whitelist()
def create_purchase_order(purchase_request):
	purchase_order_exists = frappe.db.exists('Purchase Request', {'purchase_request': purchase_request})
	if not purchase_order_exists:
		purchase_order = frappe.new_doc('Purchase Request')
		purchase_order.purchase_request = purchase_request
		purchase_order.raw_material_request = purchase_order.raw_material_request
		purchase_order.manufacturing_request = purchase_order.manufacturing_request
		purchase_order.raw_material = purchase_order.raw_material
		purchase_order.required_by = purchase_order.required_by
		purchase_order.quantity = purchase_order.quantity
		frappe.msgprint("Purchase Order created.", indicator="green", alert=1)
	else:
		frappe.throw(_('Purchase Request {0} does not exist'.format(self.name)))
