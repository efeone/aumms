# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class RawMaterialRequest(Document):

    def on_submit(self):
        if self.not_available == 1:
            if self.raw_material_request_type == 'Manufacturing Request':
                self.create_manufacturing_request()
                self.create_purchase_order()

    @frappe.whitelist()
    def create_manufacturing_request(self):
        manufacturing_request_exists = frappe.db.exists('Manufacturing Request', {'raw_material_request': self.name})
        if not manufacturing_request_exists:
            manufacturing_request = frappe.new_doc('Manufacturing Request')
            manufacturing_request.raw_material_request_type = self.raw_material_request_type
            manufacturing_request.raw_material_request = self.name
            manufacturing_request.jewellery_order = self.jewellery_order
            manufacturing_request.required_date = self.required_date
            manufacturing_request.weight = self.weight
            manufacturing_request.insert(ignore_permissions=True)
            frappe.msgprint(f"Manufacturing Request {manufacturing_request.name} created.", indicator="green", alert=1)
        else:
            frappe.throw(_('Manufacturing Request already exist for this {0}'.format(self.name)))

    @frappe.whitelist()
    def create_purchase_order(self):
        purchase_order = frappe.new_doc('Purchase Order')
        purchase_order.supplier = self.supplier

        purchase_order.append('items', {
            'item_code': self.item_name,
            'item_name': self.item_name,
            'schedule_date': self.required_date,
            'uom' : self.uom,
            'qty' :self.required_quantity,

        })
        purchase_order.insert(ignore_permissions=True)
        frappe.msgprint(f"Purchase Order created.", indicator="green", alert=1)
