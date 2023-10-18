import frappe
from frappe import _

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
        warehouse_doc.warehouse_name = 'All smith Warehouse'
        warehouse_doc.parent_warehouse = warehouse
        warehouse_doc.is_group = 1
        warehouse_doc.insert(ignore_permissions = True)
        frappe.db.commit()
