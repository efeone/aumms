# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.desk.form.assign_to import add as add_assign

class DesignRequest(Document):
		
	def autoname(self):
		if self.customer_name:
			self.name = self.customer + '-' + self.design_title + '-' + frappe.utils.today()

@frappe.whitelist()
def design_analyst_user_query(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql("""
        SELECT
            u.name
        FROM
            `tabUser`u ,
            `tabHas Role` r
        WHERE
            u.name = r.parent and
            r.role = 'Design Analyst' and
            u.enabled = 1 and
            u.name like %s
    """, ("%" + txt + "%"))

@frappe.whitelist()
def assign_design_request(doctype, docname, assign_to):
	assign_to_list = [assign_to]
	add_assign({
				"assign_to": assign_to_list,
				"doctype": doctype,
				"name": docname
			})
	frappe.db.set_value(doctype, docname, 'assigned_person', assign_to)
	frappe.db.commit()