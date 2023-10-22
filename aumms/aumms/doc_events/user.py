import frappe
from frappe.utils import has_common, get_fullname


def create_smith_warehouse(doc, method = None):
    """
    method to create personal warehouse for a smith user
    args:
        doc (class object): object of User
    """
    # checking if the user has Smith roles or if the user is administrator
    user_roles = frappe.get_roles(doc.name)
    required_roles = ["Smith", "Head of Smith"]
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
        new_warehouse.parent_warehouse = 'All smith Warehouse - EG'
        new_warehouse.save()
