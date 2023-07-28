# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class DesignRequest(Document):
		
	def autoname(self):
		
		if self.customer_name:
			self.name = self.customer + '-' + self.design_title + '-' + frappe.utils.today()





