import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def after_install():
	#Creating AuMMS specific custom fields
	create_custom_fields(get_custom_fields(), ignore_validate=True)

def after_migrate():
	after_install()

def is_setup_completed():
	if frappe.db.get_single_value("System Settings", "setup_complete"):
		return True
	else:
		return False

def setup_aumms_defaults():
	setup_completed = is_setup_completed()
	if setup_completed:
		enable_common_party_accounting()
		create_default_aumms_item_group()
		create_old_gold_aumms_item_group()
		create_all_smith_warehouse()
		create_department_for_smith()

def enable_common_party_accounting():
	"""
		method to enable common party accounting on Accounts Settings after install
	"""
	if frappe.db.exists('Accounts Settings'):
		accounts_settings_doc = frappe.get_doc('Accounts Settings')
		#set enable_common_party_accounting value as 1
		accounts_settings_doc.enable_common_party_accounting = 1
		accounts_settings_doc.save()
		frappe.db.commit()

def create_default_aumms_item_group():
	''' Method to create default AuMMS Item Group on after install '''
	if not frappe.db.exists('AuMMS Item Group', 'All AuMMS Item Group'):
		aumms_item_group_doc = frappe.new_doc('AuMMS Item Group')
		aumms_item_group_doc.name = 'All AuMMS Item Group'
		aumms_item_group_doc.item_group_name = 'All AuMMS Item Group'
		aumms_item_group_doc.is_group = 1
		aumms_item_group_doc.insert(ignore_permissions = True)
		frappe.db.commit()

def create_old_gold_aumms_item_group():
	''' Method to create Old Gold AuMMS Item Group on after install '''
	if not frappe.db.exists('AuMMS Item Group', 'AuMMS Old Gold'):
		aumms_item_group_doc = frappe.new_doc('AuMMS Item Group')
		aumms_item_group_doc.name = 'AuMMS Old Gold'
		aumms_item_group_doc.item_group_name = 'AuMMS Old Gold'
		aumms_item_group_doc.making_charge_based_on = 'Fixed'
		aumms_item_group_doc.is_group = 0
		aumms_item_group_doc.currency = 0
		aumms_item_group_doc.is_purchase_item = 1
		if frappe.db.exists('AuMMS Item Group', 'All AuMMS Item Group'):
			aumms_item_group_doc.parent_aumms_item_group = 'All AuMMS Item Group'
		aumms_item_group_doc.insert(ignore_permissions = True)
		frappe.db.commit()

def create_all_smith_warehouse():
	''' Method to create default All Smith Warehouse on after migrate '''
	default_company = frappe.db.get_single_value('Global Defaults', 'default_company')
	warehouse = frappe.get_value('Warehouse',{'warehouse_name': 'All Warehouses'})
	if not frappe.db.exists('Warehouse', {'warehouse_name': 'All Smith Warehouse'}):
		warehouse_doc = frappe.new_doc('Warehouse')
		warehouse_doc.company = default_company
		warehouse_doc.warehouse_name = 'All Smith Warehouse'
		warehouse_doc.parent_warehouse = warehouse
		warehouse_doc.is_group = 1
		warehouse_doc.insert(ignore_permissions = True)
		frappe.db.commit()

def create_department_for_smith():
	''' Method to create smith department on after migrate '''
	default_company = frappe.db.get_single_value('Global Defaults', 'default_company')
	department = frappe.get_value('Department',{'department_name': 'All Departments'})
	if not frappe.db.exists('Department', {'department_name': 'Smith'}):
		department_doc = frappe.new_doc('Department')
		department_doc.company = default_company
		department_doc.department_name = 'Smith'
		department_doc.parent_warehouse = department
		department_doc.is_group = 1
		department_doc.insert(ignore_permissions = True)
		frappe.db.commit()


def get_custom_fields():
	'''
	All AuMMS specific custom fields, grouped by the standard doctype they extend.

	This is the single source of truth for custom fields; they are created and
	kept up to date by after_install / after_migrate. Do not add them as
	Custom Field fixtures.

	Only standard (Frappe / ERPNext) doctypes belong here. Fields on AuMMS' own
	doctypes are plain fields in their DocType JSON, not custom fields.

	Within a doctype, a field must be listed after the custom field its
	insert_after points to.
	'''
	return {
		"Item": get_item_custom_fields(),
		"Item Group": get_item_group_custom_fields(),
		"UOM": get_uom_custom_fields(),
		"Department": get_department_custom_fields(),
		"Employee": get_employee_custom_fields(),
		"Work Order": get_work_order_custom_fields(),
		"Job Card": get_job_card_custom_fields(),
		"Purchase Invoice": get_purchase_invoice_custom_fields(),
		"Purchase Invoice Item": get_purchase_invoice_item_custom_fields(),
		"Purchase Receipt": get_purchase_receipt_custom_fields(),
		"Purchase Receipt Item": get_purchase_receipt_item_custom_fields(),
		"Sales Invoice": get_sales_invoice_custom_fields(),
		"Sales Invoice Item": get_sales_invoice_item_custom_fields(),
		"Sales Order": get_sales_order_custom_fields(),
		"Sales Order Item": get_sales_order_item_custom_fields(),
		"Delivery Note": get_delivery_note_custom_fields(),
		"Delivery Note Item": get_delivery_note_item_custom_fields(),
		"Stock Reconciliation": get_stock_reconciliation_custom_fields(),
		"Payment Entry": get_payment_entry_custom_fields(),
	}

def get_item_custom_fields():
	''' Custom fields added to Item '''
	return [
		{
			"fieldname": "item_type",
			"label": "Item Type",
			"fieldtype": "Link",
			"options": "Item Type",
			"insert_after": "item_group",
			"fetch_from": "item_group.item_type",
			"fetch_if_empty": 1,
			"allow_in_quick_entry": 1,
		},
		{
			"fieldname": "is_purity_item",
			"label": "Is Purity Item",
			"fieldtype": "Check",
			"insert_after": "item_type",
			"default": "0",
			"fetch_from": "item_type.is_purity_item",
			"read_only": 1,
			"hidden": 1,
		},
		{
			"fieldname": "purity",
			"label": "Purity",
			"fieldtype": "Link",
			"options": "Purity",
			"insert_after": "is_purity_item",
			"depends_on": "eval:doc.item_type && doc.is_purity_item",
			"mandatory_depends_on": "eval:doc.is_purity_item",
			"allow_in_quick_entry": 1,
		},
		{
			"fieldname": "purity_percentage",
			"label": "Purity Percentage",
			"fieldtype": "Percent",
			"insert_after": "purity",
			"fetch_from": "purity.purity_percentage",
			"depends_on": "eval:doc.is_purity_item",
			"read_only": 1,
		},
		{
			"fieldname": "making_charge_based_on",
			"label": "Making Charge Based On",
			"fieldtype": "Select",
			"options": "\nFixed\nPercentage",
			"insert_after": "item_qr_image",
			"fetch_from": "item_group.making_charge_based_on",
			"fetch_if_empty": 1,
			"depends_on": "eval:doc.is_purity_item",
			"translatable": 1,
		},
		{
			"fieldname": "making_charge_percentage",
			"label": "Making Charge Percentage",
			"fieldtype": "Percent",
			"insert_after": "making_charge_based_on",
			"fetch_from": "item_group.percentage",
			"fetch_if_empty": 1,
			"depends_on": "eval: doc.making_charge_based_on == 'Percentage' && doc.is_purity_item",
			"mandatory_depends_on": "eval: doc.making_charge_based_on == 'Percentage'",
		},
		{
			"fieldname": "making_charge",
			"label": "Making Charge",
			"fieldtype": "Currency",
			"insert_after": "making_charge_percentage",
			"fetch_from": "item_group.currency",
			"fetch_if_empty": 1,
			"depends_on": "eval: doc.making_charge_based_on == 'Fixed' && doc.is_purity_item",
			"mandatory_depends_on": "eval: doc.making_charge_based_on == 'Fixed'",
		},
		{
			"fieldname": "is_aumms_item",
			"label": "Is AuMMS Item",
			"fieldtype": "Check",
			"insert_after": "disabled",
			"read_only": 1,
		},
		{
			"fieldname": "custom_is_raw_material",
			"label": "Is Raw Material",
			"fieldtype": "Check",
			"insert_after": "is_aumms_item",
		},
		{
			"fieldname": "item_qr",
			"label": "Item QR Code",
			"fieldtype": "Attach Image",
			"options": "item_qr",
			"insert_after": "stock_uom",
		},
		{
			"fieldname": "item_qr_image",
			"label": "Item QR Code",
			"fieldtype": "Image",
			"options": "item_qr",
			"insert_after": "item_qr",
		},
		{
			"fieldname": "gold_weight",
			"label": "Gold Weight",
			"fieldtype": "Float",
			"insert_after": "warranty_period",
			"default": "0",
		},
		{
			"fieldname": "has_stone",
			"label": "Has Stone",
			"fieldtype": "Check",
			"insert_after": "weight_uom",
		},
		{
			"fieldname": "stone_weight",
			"label": "Stone Weight",
			"fieldtype": "Float",
			"insert_after": "has_stone",
			"default": "0",
			"depends_on": "has_stone",
		},
		{
			"fieldname": "stone_charge",
			"label": "Stone Charge",
			"fieldtype": "Currency",
			"insert_after": "stone_weight",
			"default": "0",
			"depends_on": "has_stone",
		},
	]

def get_item_group_custom_fields():
	''' Custom fields added to Item Group '''
	return [
		{
			"fieldname": "is_aumms_item_group",
			"label": "Is AuMMS Item Group",
			"fieldtype": "Check",
			"insert_after": "image",
			"read_only": 1,
		},
		{
			"fieldname": "item_type",
			"label": "Item Type",
			"fieldtype": "Link",
			"options": "Item Type",
			"insert_after": "column_break_5",
			"fetch_from": "parent_item_group.item_type",
			"fetch_if_empty": 1,
		},
		{
			"fieldname": "is_purity_item",
			"label": "Is Purity Item",
			"fieldtype": "Check",
			"insert_after": "item_type",
			"fetch_from": "item_type.is_purity_item",
			"read_only": 1,
			"hidden": 1,
		},
		{
			"fieldname": "making_charge_based_on",
			"label": "Making Charge Based On",
			"fieldtype": "Select",
			"options": "\nFixed\nPercentage",
			"insert_after": "is_purity_item",
			"depends_on": "eval: doc.is_purity_item",
		},
		{
			"fieldname": "percentage",
			"label": "Percentage",
			"fieldtype": "Percent",
			"insert_after": "making_charge_based_on",
			"depends_on": "eval: doc.making_charge_based_on == 'Percentage'",
			"mandatory_depends_on": "eval: doc.making_charge_based_on == 'Percentage'",
		},
		{
			"fieldname": "currency",
			"label": "Currency",
			"fieldtype": "Currency",
			"insert_after": "percentage",
			"depends_on": "eval: doc.making_charge_based_on == 'Fixed'",
			"mandatory_depends_on": "eval: doc.making_charge_based_on == 'Fixed'",
		},
		{
			"fieldname": "is_sales_item",
			"label": "Is Sales Item",
			"fieldtype": "Check",
			"insert_after": "currency",
		},
		{
			"fieldname": "is_purchase_item",
			"label": "Is Purchase Item",
			"fieldtype": "Check",
			"insert_after": "is_sales_item",
		},
	]

def get_uom_custom_fields():
	''' Custom fields added to UOM '''
	return [
		{
			# TODO: column_break_3 does not exist on UOM in v15
			"fieldname": "is_purity_uom",
			"label": "Is Purity UOM",
			"fieldtype": "Check",
			"insert_after": "column_break_3",
		},
	]

def get_department_custom_fields():
	''' Custom fields added to Department '''
	return [
		{
			"fieldname": "head_of_department",
			"label": "Head of Department",
			"fieldtype": "Link",
			"options": "Employee",
			"insert_after": "parent_department",
		},
	]

def get_employee_custom_fields():
	''' Custom fields added to Employee '''
	return [
		{
			"fieldname": "custom_warehouse",
			"label": "Warehouse",
			"fieldtype": "Link",
			"options": "Warehouse",
			"insert_after": "employee_name",
		},
	]

def get_work_order_custom_fields():
	''' Custom fields added to Work Order '''
	return [
		{
			"fieldname": "assigned_to",
			"label": "Assigned To",
			"fieldtype": "Link",
			"options": "Smith",
			"insert_after": "project",
			"reqd": 1,
		},
		{
			"fieldname": "smith_name",
			"label": "Smith Name",
			"fieldtype": "Data",
			"insert_after": "assigned_to",
			"fetch_from": "assigned_to.smith_name",
			"fetch_if_empty": 1,
		},
	]

def get_job_card_custom_fields():
	''' Custom fields added to Job Card '''
	return [
		{
			"fieldname": "assigned_to",
			"label": "Assigned To",
			"fieldtype": "Link",
			"options": "Smith",
			"insert_after": "employee",
			"fetch_from": "work_order.assigned_to",
		},
		{
			"fieldname": "assigned_employee",
			"label": "Assigned Employee",
			"fieldtype": "Link",
			"options": "Employee",
			"insert_after": "assigned_to",
			"fetch_from": "assigned_to.employee",
			"read_only": 1,
			"hidden": 1,
		},
	]

def get_purchase_invoice_custom_fields():
	''' Custom fields added to Purchase Invoice '''
	return [
		{
			"fieldname": "keep_metal_ledger",
			"label": "Keep Metal Ledger",
			"fieldtype": "Check",
			"insert_after": "supplier",
		},
	]

def get_purchase_invoice_item_custom_fields():
	''' Custom fields added to Purchase Invoice Item '''
	return [
		{
			"fieldname": "item_type",
			"label": "Item Type",
			"fieldtype": "Link",
			"options": "Item Type",
			"insert_after": "rejected_qty",
			"fetch_from": "item_code.item_type",
		},
	]

def get_purchase_receipt_custom_fields():
	''' Custom fields added to Purchase Receipt '''
	return [
		{
			"fieldname": "party_link",
			"label": "Party Link",
			"fieldtype": "Link",
			"options": "Party Link",
			"insert_after": "supplier_delivery_note",
			"read_only": 1,
		},
		{
			"fieldname": "keep_metal_ledger",
			"label": "Keep Metal Ledger",
			"fieldtype": "Check",
			"insert_after": "set_posting_time",
		},
		{
			"fieldname": "create_invoice_on_submit",
			"label": "Create Invoice on Submit",
			"fieldtype": "Check",
			"insert_after": "keep_metal_ledger",
			"read_only": 1,
			"hidden": 1,
		},
	]

def get_purchase_receipt_item_custom_fields():
	''' Custom fields added to Purchase Receipt Item '''
	return [
		{
			"fieldname": "board_rate",
			"label": "Board Rate",
			"fieldtype": "Data",
			"insert_after": "amount",
		},
		{
			"fieldname": "making_charge",
			"label": "Making Charge",
			"fieldtype": "Data",
			"insert_after": "board_rate",
		},
		{
			"fieldname": "stone_weight",
			"label": "Stone Weight",
			"fieldtype": "Data",
			"insert_after": "is_free_item",
		},
		{
			"fieldname": "stone_charge",
			"label": "Stone Charge",
			"fieldtype": "Data",
			"insert_after": "stone_weight",
		},
	]

def get_sales_invoice_custom_fields():
	''' Custom fields added to Sales Invoice '''
	return [
		{
			"fieldname": "keep_metal_ledger",
			"label": "Keep Metal Ledger",
			"fieldtype": "Check",
			"insert_after": "is_debit_note",
		},
	]

def get_sales_invoice_item_custom_fields():
	''' Custom fields added to Sales Invoice Item '''
	return [
		{
			"fieldname": "board_rate",
			"label": "Board Rate",
			"fieldtype": "Data",
			"insert_after": "amount",
		},
	]

def get_delivery_note_custom_fields():
	''' Custom fields added to Delivery Note '''
	return [
		{
			"fieldname": "keep_metal_ledger",
			"label": "Keep Metal Ledger",
			"fieldtype": "Check",
			"insert_after": "set_posting_time",
		},
	]

def get_delivery_note_item_custom_fields():
	''' Custom fields added to Delivery Note Item '''
	return [
		{
			"fieldname": "board_rate",
			"label": "Board Rate",
			"fieldtype": "Data",
			"insert_after": "amount",
		},
	]

def get_sales_order_custom_fields():
	''' Custom fields added to Sales Order '''
	return [
		{
			"fieldname": "keep_metal_ledger",
			"label": "Keep Metal Ledger",
			"fieldtype": "Check",
			"insert_after": "amended_from",
			"read_only": 1,
			"hidden": 1,
		},
	]

def get_sales_order_item_custom_fields():
	''' Custom fields added to Sales Order Item '''
	return [
		{
			"fieldname": "board_rate",
			"label": "Board Rate",
			"fieldtype": "Data",
			"insert_after": "amount",
		},
	]

def get_stock_reconciliation_custom_fields():
	''' Custom fields added to Stock Reconciliation '''
	return [
		{
			"fieldname": "keep_metal_ledger",
			"label": "Keep Metal Ledger",
			"fieldtype": "Check",
			"insert_after": "purpose",
		},
	]

def get_payment_entry_custom_fields():
	''' Custom fields added to Payment Entry '''
	return [
		{
			"fieldname": "jewellery_invoice",
			"label": "Jewellery Invoice",
			"fieldtype": "Link",
			"options": "Jewellery Invoice",
			"insert_after": "party_name",
			"read_only": 1,
			"no_copy": 1,
			"allow_on_submit": 1,
			"search_index": 1,
		},
	]

