# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from aumms.setup import create_all_smith_warehouse
from frappe.utils import get_fullname
from frappe.utils.data import has_common

# link field on Smith that holds the reference for each smith type
SMITH_REFERENCE_FIELDS = {'Employee': 'employee', 'Supplier': 'supplier'}

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
			new_warehouse.is_group = 0
			new_warehouse.parent_warehouse = get_all_smith_warehouse()
			new_warehouse.save(ignore_permissions=True)
			self.warehouse = new_warehouse.name
			frappe.db.set_value("Employee", self.employee, "custom_warehouse", new_warehouse.name)

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
@frappe.validate_and_sanitize_search_inputs
def head_of_smith_filter_query(doctype, txt, searchfield, start, page_len, filters):
	'''
		Query for Head of Smith field in Smith DocType, only employees marked as head of smith are listed
	'''
	heads_of_smith = frappe.get_all(
		'Smith',
		filters = {'is_head_of_smith': 1, 'employee': ['is', 'set']},
		pluck = 'employee'
	)
	if not heads_of_smith:
		return []
	return frappe.get_all(
		doctype,
		filters = {'name': ['in', heads_of_smith]},
		or_filters = get_search_or_filters(doctype, txt),
		fields = get_search_fields(doctype),
		order_by = 'name asc',
		start = start,
		page_length = page_len,
		as_list = True
	)

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def smith_reference_filter_query(doctype, txt, searchfield, start, page_len, filters):
	'''
		Query for Employee and Supplier fields in Smith DocType, exclude those with Smith already created
	'''
	fieldname = SMITH_REFERENCE_FIELDS.get(doctype)
	if not fieldname:
		return []

	smith_filters = {fieldname: ['is', 'set']}
	current_smith = (filters or {}).get('current_smith')
	if current_smith:
		# the Smith being edited has to keep its own employee or supplier in the list
		smith_filters['name'] = ['!=', current_smith]
	referenced = frappe.get_all('Smith', filters = smith_filters, pluck = fieldname)

	return frappe.get_all(
		doctype,
		filters = {'name': ['not in', referenced]} if referenced else None,
		or_filters = get_search_or_filters(doctype, txt),
		fields = get_search_fields(doctype),
		order_by = 'name asc',
		start = start,
		page_length = page_len,
		as_list = True
	)

def get_search_fields(doctype):
	'''
		Name and title field of the doctype, listed as value and description in the link search
	'''
	title_field = frappe.get_meta(doctype).title_field
	if title_field and title_field != 'name':
		return ['name', title_field]
	return ['name']

def get_search_or_filters(doctype, txt):
	'''
		Filters matching the typed text against the searchable fields of the doctype
	'''
	if not txt:
		return None
	return [[fieldname, 'like', f'%{txt}%'] for fieldname in get_search_fields(doctype)]

def create_user_for_smith(doc):
	'''
		Create user for smith if email is provided and smith is head of smith
	'''
	if doc.email and doc.is_head_of_smith:
		if not frappe.db.exists('User', doc.email):
			user = frappe.new_doc('User')
			user.email = doc.email
			user.first_name = doc.smith_name
			user.append('roles', {'role': 'Head of Smith'})
			user.save(ignore_permissions=True)
			frappe.msgprint('User created for this smith', alert=True, indicator='green')
