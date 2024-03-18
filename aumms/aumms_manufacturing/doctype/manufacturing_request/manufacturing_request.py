# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt
import frappe
from frappe import _
from frappe.model.document import Document
# from aumms.aumms_manufacturing.doctype.raw_material_request.raw_material_request import create_manufacturing_request


class ManufacturingRequest(Document):
	def on_submit(self):
		if self.raw_material_request_type == 'Jewellery Order':
			self.create_raw_material_request()


	def create_raw_material_request(self):
		raw_material_request_exists = frappe.db.exists('Raw Material Request', {'manufacturing_request' : self.name})
		if not raw_material_request_exists:
			raw_material_request = frappe.new_doc('Raw Material Request')
			raw_material_request.raw_material_request_type = "Jewellery Order"
			raw_material_request.manufacturing_request = self.name
			raw_material_request.jewellery_order = self.jewellery_order
			raw_material_request.required_date = self.required_date
			raw_material_request.insert(ignore_permissions = True)
			frappe.msgprint(f"Raw Material Request {raw_material_request.name} created.",indicator="green", alert=1 )
		else:
			frappe.throw(_('Manufacturing Request {0} does not exists'.format(self.name)))
