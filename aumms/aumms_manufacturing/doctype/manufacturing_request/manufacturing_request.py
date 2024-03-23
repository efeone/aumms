# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc


class ManufacturingRequest(Document):
	def before_insert(self):
		self.update_mingr_stages()
	
	def update_mingr_stages(self):
		if self.category:
			category_doc = frappe.get_doc('Item Category', self.category)
			for stage in category_doc.stages:
				self.append('manufacturing_request_stage', {
					'manufacturing_stage': stage.stage,
					'required_time': stage.required_time,
					'workstation': stage.default_workstation
				})

@frappe.whitelist()
def create_required_raw_material(source_name, target_doc=None):
	doc = get_mapped_doc(
		'Manufacturing Request',
		source_name,
		{
			'Manufacturing Request': {
				'doctype': 'Raw Material Bundle',
				"field_map": {
					"name": "manufacturing_request",
					"required_date": "item_required_date"
				}
			},
			'Manufacturing Request Stage': {
				'doctype': 'Raw Material Bundle',
				"field_map": {
					"quantity": "total_quantity",
					"total_weight": "total_weight"
				}
			}
		},
		target_doc
	)
	return doc
