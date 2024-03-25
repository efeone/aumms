# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class RawMaterialBundle(Document):
	def autoname(self):
		for raw_material_details in self.get("raw_material_details"):
			raw_material_details.raw_material_id = f"{raw_material_details.item_name}-{raw_material_details.item_type}-{raw_material_details.quantity}"


	def on_submit(self):
		self.create_raw_materiel_request()

	def create_raw_materiel_request(self):
		raw_materiel_count = 0
		for raw_material in self.raw_material_details:
			if raw_material.quantity > raw_material.available_quantity_in_stock:
				raw_materiel_request_exists = frappe.db.exists('Raw Material Request', {
				'manufacturing_request': self.manufacturing_request,
				'item_name': raw_material.item_name
	            })
				if not raw_materiel_request_exists:
					new_raw_materiel_request = frappe.new_doc('Raw Material Request')
					new_raw_materiel_request.raw_material_request_type = "Manufacturing Request"
					new_raw_materiel_request.raw_material_bundle = self.name
					new_raw_materiel_request.manufacturing_request = self.manufacturing_request
					new_raw_materiel_request.required_date = self.item_required_date
					new_raw_materiel_request.required_quantity = raw_material.quantity - raw_material.available_quantity_in_stock
					new_raw_materiel_request.item_name = raw_material.item_name
					new_raw_materiel_request.item_type = raw_material.item_type
					new_raw_materiel_request.bundle_id = raw_material.raw_material_id
					new_raw_materiel_request.insert(ignore_permissions=True)
					raw_materiel_count += 1
		frappe.msgprint(f"{raw_materiel_count} Raw Material Requests Created.", indicator="green", alert=1)
