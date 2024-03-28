# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class JewelleryJobCard(Document):
    def before_insert(self):
        self.update_item_table()

    def update_item_table(self):
        if frappe.db.exists('Raw Material Bundle', {'manufacturing_request': self.manufacturing_request}):
            raw_material_doc = frappe.get_doc('Raw Material Bundle', {'manufacturing_request': self.manufacturing_request})
            for raw_material in raw_material_doc.raw_material_details:
                self.append('item_details', {
                    'item_code': raw_material.item_name,
                    'raw_material_id' : raw_material.raw_material_id,
                    'item_type': raw_material.item_type,
                    'required_quantity': raw_material.quantity
                })
