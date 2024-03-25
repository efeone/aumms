# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class RawMaterialRequest(Document):

    def on_submit(self):
        if self.not_available == 0:
            if self.raw_material_request_type == 'Raw Material Request':
                self.create_manufacturing_request()

    def create_manufacturing_request(self):
        manufacturing_request_exists = frappe.db.exists('Manufacturing Request', {'raw_material_request': self.name})
        if not manufacturing_request_exists:
            manufacturing_request = frappe.new_doc('Manufacturing Request')
            manufacturing_request.raw_material_request_type = self.raw_material_request_type
            manufacturing_request.raw_material_request = self.name
            manufacturing_request.required_date = self.required_date
            manufacturing_request.total_weight = self.total_weight
            manufacturing_request.jewellery_order = self.jewellery_order
            manufacturing_request.insert(ignore_permissions=True)
            frappe.msgprint(f"Manufacturing Request {manufacturing_request.name} created.", indicator="green", alert=1)
        else:
            frappe.throw(_('Raw Material Request {0} does not exist'.format(self.name)))
