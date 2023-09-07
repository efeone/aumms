# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class DesignAnalysis(Document):

    def create_design_request_from_design_analysis(customer, mobile_no, design_title, delivery_date, attachment):
     #def set_design_request_values(customer, mobile_no, design_title, delivery_date, attachment):
     # Create new Design Request
        design_request = frappe.new_doc({
            "doctype": "Design Request",
            "customer_name": customer,
            "mobile_number": mobile_no,
            "self.design_details[0].Material": design_title,
            "delivery_date": delivery_date,
            "self.design_details[0].Attachment": attachment
        })

    #Save the Design Request
        design_request.insert()
        frappe.msgprint("Design Request Created: {}".format(design_request.name), indicator="green", alert=1)
        return design_request.name


    def autoname(self):
          if self.customer_name:
               self.name = self.customer_name + '-' + self.item + '-' + frappe.utils.today()

@frappe.whitelist()
def create_aumms_item_from_design_analysis(item_code, item_group, purity):
    def set_missing_values(item_code, item_group, purity):
        pass
    # Create a new Aumms Item document
    aumms_item = frappe.get_doc({
        "doctype": "AuMMS Item",
        "item_name": item_code,
        "item_code": item_code,  
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


    