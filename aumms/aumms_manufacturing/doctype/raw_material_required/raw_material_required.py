# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class RawMaterialRequired(Document):
	def validate(self):
		self.validate_date()
		self.validate_weight()

	def validate_date(self):
	    if self.raw_material_required_date and self.item_required_date and self.raw_material_required_date >= self.item_required_date:
	        frappe.throw(_('The Raw Material Required Date must be earlier than the Item Required Date'))


	def validate_weight(self):
		if self.total_weight != self.total_raw_material_weight:
			frappe.throw(_('The Total Raw Material weight Must be Equal to Total Weight'))
