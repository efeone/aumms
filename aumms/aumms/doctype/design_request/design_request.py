# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
# from frappe.desk.form.assign_to import add as add_assignment

class DesignRequest(Document):
    def autoname(self):
        if self.customer_name:
            self.name = f"{self.customer_name}-{self.design_title}-{frappe.utils.today()}"

# Remove the assign_permission_role function, as it is not needed anymore

def after_insert(doc, method):
    # Remove the assign_to check in after_insert, as it will be handled in JavaScript now
    pass

# The doc_events dictionary remains unchanged
doc_events = {
    "Design Request": {
        "after_insert": "aumms.aumms.doctype.design_request.design_request.after_insert",
    }
}





