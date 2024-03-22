# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

class ItemCategory(Document):

    def after_insert(self):
        self.update_stages()

    def update_stages(self):
        if self.manufacturing_stage_template:
            manufacturing_stage_template = frappe.get_doc("Manufacturing Stage Template", self.manufacturing_stage_template)
            for manufacturing_stage in manufacturing_stage_template.manufacturing_stages:
                self.append("stages", {
                    "stage": manufacturing_stage.stage,
                    "default_workstation": manufacturing_stage.default_workstation,
                    "required_time": manufacturing_stage.required_time
                })
            self.save()
