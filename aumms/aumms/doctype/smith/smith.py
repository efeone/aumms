# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from aumms.setup import create_all_smith_warehouse
from frappe.utils import get_fullname
from frappe.utils.data import has_common

class Smith(Document):
	def before_insert(self):
		self.create_smith_warehouse()
		
	def validate(self):
		create_user_for_smith(self)
	
	def create_smith_warehouse(self):
		"""
		method to create personal warehouse for a smith user
		"""
		if not self.warehouse:
			# generating the warehouse name
			new_warehouse = frappe.new_doc("Warehouse")
			req_warehouse_name = f"{self.smith_name} - Head of Smith" if self.is_head_of_smith else f"{self.smith_name} - Smith"

			# creating a new warehouse
			new_warehouse.warehouse_name = req_warehouse_name
			if self.is_head_of_smith:
				new_warehouse.is_group = 1
				new_warehouse.parent_warehouse = get_all_smith_warehouse()
			else:
				head_of_smith = frappe.db.exists('Smith', {'employee':self.head_of_smith})
				if not head_of_smith:
					frappe.throw(_(f'Smith not found for {self.head_of_smith}'))
				head_of_smith_warehouse = frappe.db.get_value('Smith', head_of_smith, 'warehouse')
				if not head_of_smith_warehouse:
					frappe.throw(_(f'No Warehouse found for Head of Smith {head_of_smith}'))
				new_warehouse.parent_warehouse = head_of_smith_warehouse

			new_warehouse.save(ignore_permissions=True)
			self.warehouse = new_warehouse.name

def get_all_smith_warehouse():
	all_smith_warehouse = frappe.db.exists("Warehouse", {'name':['like','%all Smith%'], 'is_group':1})

	#creating the all smith warehouse if it doesn't exist in the system
	if not all_smith_warehouse:
		create_all_smith_warehouse()
		all_smith_warehouse = frappe.db.exists("Warehouse", {'name':['like','%all Smith%'], 'is_group':1})

	if all_smith_warehouse:
		return all_smith_warehouse
	else:
		frappe.throw(_('All Smith Warehouse not found, Please contact System Manager'))

@frappe.whitelist()
def head_of_smith_filter_query(doctype, txt, searchfield, start, page_len, filters):
	'''
		Query for Head of Smith field in Smith DocType
	'''
	return frappe.db.sql('''
		SELECT
			employee
		FROM
			tabSmith
		WHERE
			is_head_of_smith = 1
	''')

@frappe.whitelist()
def smith_reference_filter_query(doctype, txt, searchfield, start, page_len, filters):
	'''
		Query for Employee and Supplier fields in Smith DocType
	'''
	return frappe.db.sql('''
		SELECT
			name
		FROM
			{tab_of_doctype}
		WHERE
			name
		NOT IN
			(
				SELECT
					{doctype}
				FROM
					tabSmith
			)
	'''.format(tab_of_doctype = f'tab{doctype}', doctype = doctype.lower()))

def create_user_for_smith(doc):
	if doc.email:
		user = frappe.new_doc('User')
		user.email = doc.email
		user.first_name = doc.smith_name
		user.append('roles', {'role': 'Head of Smith'})
		user.save(ignore_permissions = True)
		frappe.msgprint('User created for this smith', alert=True, indicator='green')

