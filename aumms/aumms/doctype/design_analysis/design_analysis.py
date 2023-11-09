# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.desk.form.assign_to import add as add_assign
from aumms.aumms.utils import create_notification_log

class DesignAnalysis(Document):
    def autoname(self):
          if self.customer_name:
               self.name = self.customer_name + '-' + self.item_code + '-' + frappe.utils.today()
    def on_update(self):
        design_request_doc = frappe.get_doc("Design Request", self.design_request)
        design_request_doc.status = self.status
        design_request_doc.save()
        frappe.db.commit()

@frappe.whitelist()
def create_bom_function(doctype, docname,assign_to):
    if frappe.db.exists('Design Analysis', docname):
        doc = frappe.get_doc('Design Analysis', docname)
        bom = frappe.new_doc('BOM')
        bom.item = doc.item
        for row in doc.verified_item:
             bom_row = bom.append('items')
             bom_row.item_code = row.item
             bom_row.uom = row.unit_of_measure
             bom_row.qty = row.quantity
        bom.flags.ignore_mandatory = True
        bom.save(ignore_permissions=True)
        assign_to_list = [assign_to]
        add_assign({
                "assign_to": assign_to_list,
                "doctype": bom.doctype,
                "name": bom.name
            })
        frappe.db.commit()
        frappe.msgprint("BOM Created", indicator="green", alert=1)
        #Send system notification and email to assignee
        subject = "New BOM request received"
        content = "You've been assigned a new BOM for work order creation. Please review it at your earliest convenience."
        create_notification_log(doctype, docname, assign_to, subject, content)
        return True
        
    else:
        return False

@frappe.whitelist()
def head_of_smith_user_query(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql("""
        SELECT
            u.name
        FROM
            `tabUser`u ,
            `tabHas Role` r
        WHERE
            u.name = r.parent and
            r.role = 'Head of Smith' and
            u.enabled = 1 and
            u.name like %s
    """, ("%" + txt + "%"))

@frappe.whitelist()
def create_aumms_item_from_design_analysis(customer_expected_weight, item, item_group, purity):
    #Calculate Item Code to set as docname
    weight = float(customer_expected_weight)
    weight = int(weight*1000)
    weight_with_zero = str(weight).zfill(6)
    doc_name = item + '-' + weight_with_zero
    # Create a new Aumms Item document
    aumms_item = frappe.get_doc({
        "doctype": "AuMMS Item",
        "item_name": item,
        "item_code": doc_name,
        "item_group": item_group,
        "purity": purity
    })

    # Save the Aumms Item document
    aumms_item.insert()

    frappe.msgprint("AuMMS Item Created: {}".format(aumms_item.name), indicator="green", alert=1)

    return aumms_item.name

@frappe.whitelist()
def fetch_design_details(parent):
	design_details = frappe.get_all(
		'Design Details',
		filters={'parenttype': 'Design Request', 'parent': parent},
		fields=['material', 'item_type', 'purity', 'unit_of_measure', 'quantity', 'is_customer_provided']
	)

	return design_details

@frappe.whitelist()
def supervisor_user_query(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql("""
        SELECT
            u.name
        FROM
            `tabUser`u ,
            `tabHas Role` r
        WHERE
            u.name = r.parent and
            r.role = 'Supervisor' and
            u.enabled = 1 and
            u.name like %s
    """, ("%" + txt + "%"))

@frappe.whitelist()
def create_design_request(design_analysis):
    doc = frappe.get_doc('Design Analysis', design_analysis)
    if doc.dr_required_check == 1:
        for design_detail in doc.design_details:
            if design_detail.dr_required == 1:
                design_request = frappe.new_doc('Design Request')
                design_request.customer = doc.customer_name
                design_request.mobile_no = doc.mobile_no
                design_request.design_title = design_detail.material
                design_request.delivery_date = frappe.utils.today()
                design_request.flags.ignore_mandatory = True
                design_request.save(ignore_permissions=True)
                frappe.msgprint("Design Request Created for the material {}".format(design_request.design_title), indicator="green", alert=1)

@frappe.whitelist()
def assign_design_analysis(doctype, docname, assign_to):
    assign_to_list = [assign_to]
    add_assign({
    "assign_to": assign_to_list,
    "doctype": doctype,
    "name": docname
    })