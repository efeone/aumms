# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt
import frappe
from frappe import _
from frappe.model.document import Document


class RawMaterialBundle(Document):
	def autoname(self):
		for items in self.get("items"):
			items.raw_material_id = f"{items.item}-{self.stage}-{items.required_weight}"

	def validate(self):
		for item in self.items:
			if item.available_quantity > item.required_quantity:
				self.raw_material_available = 1
			else:
				self.raw_material_available = 0

	def on_submit(self):
		self.mark_as_raw_material_bundle_created(created = 1)

	def on_cancel(self):
		self.mark_as_raw_material_bundle_created(created = 0)

	def mark_as_raw_material_bundle_created(self, created):
		if frappe.db.exists('Manufacturing Request', self.manufacturing_request):
			manufacturing_request = frappe.get_doc('Manufacturing Request', self.manufacturing_request)
			if manufacturing_request:
				updated = False
				for stage in manufacturing_request.manufacturing_stages:
					if stage.manufacturing_stage == self.stage:
						stage.raw_material_bundle_created = created
						frappe.db.set_value('Manufacturing  Stage', stage.name, 'raw_material_bundle_created', created)
						frappe.db.set_value('Manufacturing  Stage', stage.name, 'raw_material_available', created)
						break


@frappe.whitelist()
def create_raw_material_request(docname):
    raw_material_bundle = frappe.get_doc("Raw Material Bundle", docname)
    uom = frappe.get_single("AuMMS Settings").get("metal_ledger_uom")
    raw_material_request_count = 0
    for raw_material in raw_material_bundle.items:
        raw_material_request_exists = frappe.db.exists('Raw Material Request', {
            'manufacturing_request': raw_material_bundle.manufacturing_request,
            'item': raw_material.item
        })
        if not raw_material_request_exists:
            new_raw_material_request = frappe.new_doc('Raw Material Request')
            new_raw_material_request.raw_material_request_type = "Raw Material Request"
            new_raw_material_request.raw_material_bundle = raw_material_bundle.name
            new_raw_material_request.manufacturing_request = raw_material_bundle.manufacturing_request
            new_raw_material_request.required_quantity = raw_material.required_quantity - raw_material.available_quantity
            new_raw_material_request.required_date = raw_material_bundle.required_date
            new_raw_material_request.uom = raw_material_bundle.uom
            new_raw_material_request.item_type = raw_material_bundle.type
            new_raw_material_request.purity = raw_material_bundle.purity
            new_raw_material_request.supervisor_warehouse = raw_material_bundle.supervisor_warehouse
            new_raw_material_request.bundle_id = raw_material.raw_material_id
            new_raw_material_request.uom = uom
            raw_material_details = {
                'item': raw_material.item,
                'warehouse': raw_material.warehouse,
                'required_quantity': raw_material.required_quantity,
                'available_quantity': raw_material.available_quantity,
                'required_weight': raw_material.required_weight,
                'available_weight': raw_material.available_weight,
            }
            new_raw_material_request.append('raw_material_details', raw_material_details)
            new_raw_material_request.insert(ignore_permissions=True)
            raw_material_request_count += 1

        else:
            frappe.throw(_("Raw Material Request already exists for item {0}").format(raw_material.item))
    frappe.msgprint(f"{raw_material_request_count} Raw Material Requests Created.", indicator="green", alert=True)
