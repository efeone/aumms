# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

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





