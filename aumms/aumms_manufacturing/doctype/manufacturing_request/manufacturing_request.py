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
	def update_previous_stage(self, idx):
		for stage in self.manufacturing_request_stage:
			if stage.idx == idx:
				if stage.awaiting_raw_material:
					prev_row = stage.idx - 1
					for row in self.manufacturing_request_stage:
						if row.idx == prev_row:
							return row.manufacturing_stage
