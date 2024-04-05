# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt
import frappe
from frappe import _
from frappe.model.document import Document

class JewelleryOrder(Document):

	def on_submit(self):
		self.create_manufacturing_request()

	def on_update(self):
		self.out_for_delivery_check()

	def create_manufacturing_request(self):
		"""Create Manufacturing Request For Jewellery Order"""
		manufacturing_request_exists = frappe.db.exists('Manufacturing Request', {"jewellery_order": self.name})
		if not manufacturing_request_exists:
			for item in self.jewellery_order_items:
				if item.is_available == 0 :
					new_manufacturing_request = frappe.new_doc('Manufacturing Request')
					new_manufacturing_request.raw_material_request_type = "Jewellery Order"
					new_manufacturing_request.jewellery_order = self.name
					new_manufacturing_request.jewellery_order_design = self.design
					new_manufacturing_request.required_date = self.required_date
					new_manufacturing_request.uom = self.uom
					new_manufacturing_request.total_weight = item.weight
					new_manufacturing_request.purity = self.purity
					new_manufacturing_request.type = self.type
					new_manufacturing_request.quantity = self.quantity
					new_manufacturing_request.category = self.category
					new_manufacturing_request.item_name = f"{self.category}-{self.type}"
					new_manufacturing_request.insert(ignore_permissions=True)
					item.requested_for_manufacturing = 1
					frappe.msgprint(f"Manufacturing Request {new_manufacturing_request.name} Created.", indicator="green", alert=1)
		else:
			frappe.throw(_('Manufacturing request for Jewellery Order {0} already exists'.format(self.name)))

	def out_for_delivery_check(self):
	    if frappe.db.exists('Customer Jewellery Order', {'name': self.customer_jewellery_order, 'out_for_delivery': 0}):
	        customer_jewellery_order = frappe.get_doc('Customer Jewellery Order', self.customer_jewellery_order)
	        if customer_jewellery_order:
	            jewellery_order_list = frappe.db.sql("""
	                SELECT
	                    name,
	                    finished
	                FROM
	                    `tabJewellery Order`
	                WHERE
	                    customer_jewellery_order = %s
	            """, (self.customer_jewellery_order,), as_dict=True)

	            all_finished = all(jewellery_order['finished'] == 1 for jewellery_order in jewellery_order_list)
	            if all_finished:
	                frappe.db.set_value('Customer Jewellery Order', self.customer_jewellery_order, 'out_for_delivery', 1)
	            else:
	                frappe.db.set_value('Customer Jewellery Order', self.customer_jewellery_order, 'out_for_delivery', 0)
