# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class ItemCategory(Document):

    def before_save(self):
        self.update_stages()

    def update_stages(self):
        """Fetches stages data from Manufacturing Stage Template and add it in Item Category's child table"""
        if self.manufacturing_stage_template:
            manufacturing_stage_template = frappe.get_doc(
                "Manufacturing Stage Template", self.manufacturing_stage_template
            )
            for (
                manufacturing_stage
            ) in manufacturing_stage_template.manufacturing_stages:
                if not frappe.db.exists(
                    "Manufacturing Stage Table",
                    {
                        "parent": self.name,
                        "stage": manufacturing_stage.stage,
                        "default_workstation": manufacturing_stage.default_workstation,
                        "required_time": manufacturing_stage.required_time,
                    },
                ):
                    self.append(
                        "stages",
                        {
                            "stage": manufacturing_stage.stage,
                            "default_workstation": manufacturing_stage.default_workstation,
                            "required_time": manufacturing_stage.required_time,
                        },
                    )
