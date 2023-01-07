# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _


class Purity(Document):
	def validate(self):
		self.validate_purity_percentage()

	def validate_purity_percentage(self):
		#Method to validate Purity Percentage#
		if self.purity_percentage < 0 or self.purity_percentage > 100:
			frappe.throw(
				title = _('ALERT !!'),
				msg = _(' Purity Percentage must range from 0 to 100')
				)
