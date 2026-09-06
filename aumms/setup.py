import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def after_install():
    #Creating AuMMS specific custom fields
    create_custom_fields(get_stock_reconciliation_custom_fields(), ignore_validate=True)
    create_custom_fields(get_metal_ledger_custom_fields(), ignore_validate=True)
    create_custom_fields(get_purchase_receipt_custom_fields(), ignore_validate=True)
    create_custom_fields(get_sales_invoice_custom_fields(), ignore_validate=True)
    create_custom_fields(get_jewellery_invoice_custom_fields(), ignore_validate=True)
    create_custom_fields(get_sales_order_custom_fields(), ignore_validate=True)
    create_custom_fields(get_payment_entry_custom_fields(), ignore_validate=True)

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



def get_stock_reconciliation_custom_fields():
    '''
    Custom fields that need to be added to the Stock Reconciliation Doctype
    '''
    return {
        "Stock Reconciliation": [
            {
                "fieldname": "keep_metal_ledger",
                "fieldtype": "Check",
                "label": "Keep Metal Ledger",
                "insert_after": "purpose"
            }
        ]
    }

def get_metal_ledger_custom_fields():
    '''
    Custom fields that need to be added to the Metal Ledger Entry Doctype
    '''
    return {
        "Metal Ledger Entry": [
            {
            "fieldname": "entry_type",
            "fieldtype": "Data",
            "label": "Entry Type",
            "insert_after": "voucher_type",
            "read_only":1
            }
        ]
    }


def get_purchase_receipt_custom_fields():
    '''
    Custom fields that need to be added to the Purchase Receipt Doctype
    '''
    return {
        "Purchase Receipt":[

        ],
        "Purchase Receipt Item" : [
            {
            "fieldname": "board_rate",
            "fieldtype": "Data",
            "label": "Board Rate",
            "insert_after": "amount"
            },
            {
            "fieldname": "stone_weight",
            "fieldtype": "Data",
            "label": "Stone Weight",
            "insert_after": "is_free_item"
            },
            {
            "fieldname": "stone_charge",
            "fieldtype": "Data",
            "label": "Stone Charge",
            "insert_after": "stone_weight"
            },
            {
            "fieldname": "making_charge",
            "fieldtype": "Data",
            "label": "Making Charge",
            "insert_after": "board_rate"
            }

        ]
    }


def get_sales_invoice_custom_fields():
    '''
    Custom fields that need to be added to the Sales Invoice Doctype
    '''
    return {
        "Sales Invoice": [
            
        ],
        "Sales Invoice Item": [
            {
                "fieldname": "board_rate",
                "fieldtype": "Data",
                "label": "Board Rate",
                "insert_after": "amount"
            }
        ]
    }


def get_jewellery_invoice_custom_fields():
    return {
        "Jewellery Invoice": [
            {
                "fieldname": "discounts",
                "fieldtype": "Section Break",
                "label": "Discounts",
                "insert_after": "stone_details"
            },
            {
                "fieldname": "discount_amount",
                "fieldtype": "Currency",
                "label": "Discount Amount",
                "insert_after": "discounts"
            },
            {
                "fieldname": "discount_column_break",
                "fieldtype": "Column Break",
                "label": "",
                "insert_after": "discount_amount"
            }
        ]
    }



def get_payment_entry_custom_fields():
    '''
    Custom fields that need to be added to the Payment Entry Doctype
    '''
    return {
        "Payment Entry": [
            {
                "fieldname": "jewellery_invoice",
                "fieldtype": "Link",
                "label": "Jewellery Invoice",
                "options": "Jewellery Invoice",
                "insert_after": "party_name",
                "read_only": 1,
                "no_copy": 1,
                "allow_on_submit": 1,
                "search_index": 1
            }
        ]
    }


def get_sales_order_custom_fields():
    '''
    Custom fields that need to be added to the Sales Order Doctype
    '''
    return {
        "Sales Order": [
            
        ],
        "Sales Order Item": [
            {
                "fieldname": "board_rate",
                "fieldtype": "Data",
                "label": "Board Rate",
                "insert_after": "amount"
            }
        ]
    }