# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class PurityConversionTool(Document):
	def validate(self):
		frappe.throw(_('No Permision To Save!'))
