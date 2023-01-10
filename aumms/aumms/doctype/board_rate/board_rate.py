# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class BoardRate(Document):
	def validate(self):

		# check uom is a purity uom
		if self.uom:
			uom_is_a_purity_uom(self.uom)

		# check validation over date
		time_validation_for_boardrate(self.date, self.time, self.item_type)

def uom_is_a_purity_uom(uom):
	"""
	function to check uom is a purity uom
		args:
			uom: name of uom document
		output: a message iff uom is not a purity uom
	"""
	if not frappe.db.exists('UOM', {'name': uom, 'is_purity_uom': 1}):
		frappe.throw(_('{} is not a purity uom'.format(uom)))

def time_validation_for_boardrate(date, time, item_type):
	"""
	function to validate date for board rate over item type
	"""

	if frappe.db.exists('Board Rate', {'date': date, 'time': time, 'item_type': item_type, 'docstatus': 1}):
		frappe.throw(_("{}'s board rate is already set on {} at {} ".format(item_type, date, time)))
