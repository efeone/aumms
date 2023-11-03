import frappe
from frappe.utils import has_common, get_fullname
from frappe import _
from aumms.setup import is_setup_completed, create_all_smith_warehouse


def create_smith_warehouse(doc, method = None):
    """
    method to create personal warehouse for a smith user
    args:
        doc (class object): object of User
    """
    # checking if the user has Smith roles or if the user is administrator
    user_roles = frappe.get_roles(doc.name)
    required_roles = ["Smith", "Head of Smith"]

    if not is_setup_completed():
        return

    if not has_common(user_roles, required_roles) or doc.name == 'Administrator':
        return

    # generating the warehouse name
    user_fullname = get_fullname(doc.name)
    new_warehouse = frappe.new_doc("Warehouse")
    req_warehouse_name = f"{user_fullname} - Smith"

    # checking if the warehouse already exist
    warehouse = frappe.db.exists("Warehouse", {"email_id": doc.name, 'parent_warehouse':'All smith Warehouse - EG'})
    if warehouse:
        warehouse_doc = frappe.get_doc("Warehouse", warehouse)
        # renaming the warehouse if the user's full name was changed
        if not warehouse_doc.warehouse_name == req_warehouse_name:
            warehouse_doc.warehouse_name = req_warehouse_name
            warehouse_doc.save()
    else:
        # creating a new warehouse
        new_warehouse.warehouse_name = req_warehouse_name
        new_warehouse.email_id = doc.name
        parent_warehouse_name = frappe.db.exists("Warehouse", {'name':['like','%all Smith%'], 'is_group':1})

        #creating the all smith warehouse if it doesn't exist in the system
        if not parent_warehouse_name:
            create_all_smith_warehouse()
            parent_warehouse_name = frappe.db.exists("Warehouse", {'name':['like','%all Smith%'], 'is_group':1})

        if parent_warehouse_name:
            new_warehouse.parent_warehouse = parent_warehouse_name
            new_warehouse.save()
        else:
            frappe.throw(_('All Smith Warehouse not found, Please contact System Manager'))
