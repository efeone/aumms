# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

#Fields used to map AuMMS Item to Item
aumms_item_fields = ['item_code', 'item_name', 'item_type', 'stock_uom', 'disabled', 'is_stock_item', 'making_charge_based_on', 'making_charge_percentage', 'making_charge', 'purity', 'purity_percentage', 'is_purity_item', 'description', 'weight_per_unit', 'weight_uom', 'is_purchase_item', 'purchase_uom', 'is_sales_item', 'sales_uom']

class AuMMSItem(Document):
	def after_insert(self):
		''' Method to create Item from AuMMS Item '''
		create_or_update_item(self)

	def on_update(self):
		''' Method to update created Item on changes of AuMMS Item '''
		create_or_update_item(self, self.item)

def create_or_update_item(self, item=None):
	''' Method to create or update Item from AuMMS Item '''
	item_group = frappe.db.get_value('AuMMS Item Group', self.item_group, 'item_group')
	if not item:
		#Case of new Iteam
		if not frappe.db.exists('Item', self.name):
			#Creating new Item object
			item_doc = frappe.new_doc('Item')
		else:
			#Case of exception
			return 0
	else:
		#Case of existing Item
		if frappe.db.exists("Item", item):
			#Creating existing Item object
			item_doc = frappe.get_doc('Item', item)
		else:
			#Case of exception
			return 0

	# Check Item Group existance and set Item Group
	if item_group:
		item_doc.set('item_group', item_group)

	# Set values to Item from AuMMS Item
	for aumms_item_field in aumms_item_fields:
		item_doc.set(aumms_item_field, self.get(aumms_item_field))

	#Clear and Set UOMs to Item
	item_doc.uoms = []
	for uom in self.uoms:
		row = item_doc.append('uoms')
		row.uom = uom.uom
		row.conversion_factor = uom.conversion_factor

	if not item:
		# Case of new Item
		item_doc.insert(ignore_permissions = True)
		# Set Item Group link to AuMMS Item Group
		frappe.db.set_value('AuMMS Item', self.name, 'item', item_doc.name)
	elif frappe.db.exists("Item", item):
		# case of updating existing Item
		item_doc.save(ignore_permissions = True)
	frappe.db.commit()
