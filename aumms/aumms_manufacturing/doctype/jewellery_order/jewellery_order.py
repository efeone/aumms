# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt
import frappe
from frappe import _
from frappe.model.document import Document


class JewelleryOrder(Document):

	def on_submit(self):
		if self.quantity > self.available_quantity_in_stock:
			self.create_manufacturing_request()

	def create_manufacturing_request(self):
	    """Create Manufacturing Request For Jewellery Order"""
	    manufacturing_request_exists = frappe.db.exists('Manufacturing Request', {"jewellery_order": self.name})
	    if not manufacturing_request_exists:
	        new_manufacturing_request = frappe.new_doc('Manufacturing Request')
	        new_manufacturing_request.raw_material_request_type = "Jewellery Order"
	        new_manufacturing_request.jewellery_order = self.name
	        new_manufacturing_request.jewellery_order_design = self.design_attachment
	        new_manufacturing_request.required_date = self.required_date
	        new_manufacturing_request.total_weight = self.total_weight
	        if self.stock_available:
	            if self.quantity >= self.available_quantity_in_stock:
	                total_quantity = self.quantity - self.available_quantity_in_stock
	            else:
	                total_quantity = self.available_quantity_in_stock - self.quantity
	        else:
	            total_quantity = self.quantity
	        new_manufacturing_request.quantity = total_quantity
	        new_manufacturing_request.insert(ignore_permissions=True)
	        frappe.msgprint(f"Manufacturing Request {new_manufacturing_request.name} Created.", indicator="green", alert=1)
	    else:
	        frappe.throw(_('Manufacturing request for Jewellery Order {0} already exists'.format(self.name)))
