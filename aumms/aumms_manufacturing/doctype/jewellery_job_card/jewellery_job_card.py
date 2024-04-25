# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class JewelleryJobCard(Document):

    def before_insert(self):
        self.update_item_table()

    def on_submit(self):
        self.mark_as_completed(completed=1)

    def on_cancel(self):
        self.mark_as_completed(completed=0)

    def update_item_table(self):
        if frappe.db.exists('Raw Material Bundle', {'manufacturing_request': self.manufacturing_request}):
            raw_material_doc = frappe.get_doc('Raw Material Bundle', {'manufacturing_request': self.manufacturing_request})
            for raw_material in raw_material_doc.raw_material_details:
                self.append('item_details', {
                    'item_code': raw_material.item_name,
                    'raw_material_id' : raw_material.raw_material_id,
                    'item_type': raw_material.item_type,
                    'required_quantity': raw_material.quantity,
                })

    def mark_as_completed(self, completed):
        if frappe.db.exists('Manufacturing Request', self.manufacturing_request):
            manufacturing_request = frappe.get_doc('Manufacturing Request', self.manufacturing_request)
            if manufacturing_request:
                updated = False
                for stage in manufacturing_request.manufacturing_stages:
                    if stage.manufacturing_stage == self.manufacturing_stage:
                        stage.completed = completed
                        frappe.db.set_value('Manufacturing  Stage', stage.name, 'completed', completed)
                        manufacturing_request.mark_as_finished()
                        break
