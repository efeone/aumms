# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.nestedset import NestedSet

class AuMMSItemGroup(NestedSet):
	def autoname(self):
		''' Method to create Item Group from AuMMS Item Group '''
		if self.item_type:
			self.name = self.item_group_name + '-' + self.item_type
		else:
			self.name = self.item_group_name

	def after_insert(self):
		''' Method to create Item Group from AuMMS Item Group '''
		if not frappe.db.exists('Item Group', self.name):
			item_group_doc = frappe.new_doc('Item Group')
			item_group_doc.item_group_name = self.item_group_name
			item_group_doc.is_group = self.is_group
			item_group_doc.item_type = self.item_type
			item_group_doc.making_charge_based_on = self.making_charge_based_on
			item_group_doc.percentage = self.percentage
			item_group_doc.currency = self.currency
			item_group_doc.is_purity_item = self.is_purity_item
			item_group_doc.is_sales_item = self.is_sales_item
			item_group_doc.is_purchase_item = self.is_purchase_item
			item_group_doc.is_purchase_item = self.is_purchase_item
			if self.parent_aumms_item_group:
				if frappe.db.exists('Item Group', self.parent_aumms_item_group):
					item_group_doc.parent_item_group = self.parent_aumms_item_group
			item_group_doc.insert(ignore_permissions = True)
			#Set Item Group link to AuMMS Item Group
			frappe.db.set_value('AuMMS Item Group', self.name, 'item_group', item_group_doc.name)
			frappe.db.commit()

	def on_update(self):
		''' Method to update created Item Group on changes of AuMMS Item Group '''
		if self.item_group and frappe.db.exists('Item Group', self.item_group):
			item_group_doc = frappe.get_doc('Item Group', self.item_group)
			item_group_doc.item_group_name = self.item_group_name
			item_group_doc.is_group = self.is_group
			item_group_doc.item_type = self.item_type
			item_group_doc.making_charge_based_on = self.making_charge_based_on
			item_group_doc.percentage = self.percentage
			item_group_doc.currency = self.currency
			item_group_doc.is_purity_item = self.is_purity_item
			item_group_doc.is_sales_item = self.is_sales_item
			item_group_doc.is_purchase_item = self.is_purchase_item
			item_group_doc.is_purchase_item = self.is_purchase_item
			if self.parent_aumms_item_group:
				if frappe.db.exists('Item Group', self.parent_aumms_item_group):
					item_group_doc.parent_item_group = self.parent_aumms_item_group
			item_group_doc.save(ignore_permissions = True)
			frappe.db.commit()
