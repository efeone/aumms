# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.desk.form.assign_to import add as add_assignment

class ManufacturingRequest(Document):

	def autoname(self):
		self.title = f"{self.purity}  {self.expected_weight} {self.uom}  {self.type}  {self.category}"

	def before_insert(self):
		self.update_manufacturing_stages()

	def before_submit(self):
		self.send_notification_to_owner()

	def on_update_after_submit(self):
		self.mark_as_finished()

	def on_submit(self):
		self.mark_as_finished_in_jewellery_order()
		self.manufacturing_request_finished(finished = 1)

	def on_cancel(self):
		self.manufacturing_request_finished(finished = 0)

	def update_manufacturing_stages(self):
		if self.category:
			category_doc = frappe.get_doc('Item Category', self.category)
			for stage in category_doc.stages:
				self.append('manufacturing_stages', {
					'manufacturing_stage': stage.stage,
					'required_time': stage.required_time,
					'workstation': stage.default_workstation
		        })

	def send_notification_to_owner(self):
		for stage in self.manufacturing_stages:
			if stage.smith:
				subject = "Manufacturing Stage Assigned"
				content = f"Manufacturing Stage {stage.manufacturing_stage} is Assigned to {stage.smith}"
				for_user = self.owner
				create_notification_log(self.doctype, self.name, for_user, subject, content, 'Alert')

	def mark_as_finished(self):
		finished=1
		for stage in self.manufacturing_stages:
			if not stage.completed:
				finished = 0
				break
		frappe.db.set_value('Manufacturing Request', self.name, 'finished', finished)

	def mark_as_finished_in_jewellery_order(self):
	    if frappe.db.exists('Jewellery Order', self.jewellery_order):
	        jewellery_order_doc = frappe.get_doc('Jewellery Order', self.jewellery_order)
	        if self.docstatus == 1:
	            linked_manufacturing_requests = frappe.get_all(
	                'Manufacturing Request',
	                filters={'jewellery_order': self.jewellery_order},
	                fields=['name', 'docstatus']
	            )
	            all_submitted = all(mr['docstatus'] == 1 for mr in linked_manufacturing_requests)
	            if all_submitted:
	                frappe.db.set_value('Jewellery Order', self.jewellery_order, 'finished', 1)
	                frappe.db.commit()
	            else:
	                frappe.msgprint("Not all Manufacturing Requests are submitted yet.")

	def manufacturing_request_finished(self, finished):
	    if frappe.db.exists('Jewellery Order', self.jewellery_order):
	        jewellery_order = frappe.get_doc('Jewellery Order', self.jewellery_order)
	        if jewellery_order:
	            updated = False
	            for item in jewellery_order.jewellery_order_items:
	                if item.weight == self.expected_weight:
	                    item.manufacturing_request_finished = finished
	                    frappe.db.set_value('Jewellery Order Item', item.name, 'manufacturing_request_finished', finished)
	                    break

	@frappe.whitelist()
	def update_previous_stage(self, idx):
		for stage in self.manufacturing_stages:
			if stage.idx == idx:
				if stage.previous_stage_completed:
					prev_row = stage.idx - 1
					for row in self.manufacturing_stages:
						if row.idx == prev_row:
							return row.manufacturing_stage

	@frappe.whitelist()
	def create_jewellery_job_card(self, stage_row_id):
	    stage = frappe.get_doc('Manufacturing  Stage', stage_row_id)
	    jewellery_job_card_exists = frappe.db.exists('Jewellery Job Card', {'manufacturing_request': self.name, 'manufacturing_stage': stage.manufacturing_stage})
	    if not jewellery_job_card_exists:
	        smith_email = frappe.db.get_value('Employee', stage.smith, 'user_id')
	        new_jewellery_job_card = frappe.new_doc('Jewellery Job Card')
	        new_jewellery_job_card.manufacturing_request = self.name
	        new_jewellery_job_card.smith = stage.smith
	        new_jewellery_job_card.work_station = stage.workstation
	        new_jewellery_job_card.required_date = self.required_date
	        new_jewellery_job_card.purity = self.purity
	        new_jewellery_job_card.expected_weight = self.expected_weight
	        new_jewellery_job_card.uom = self.uom
	        new_jewellery_job_card.type = self.type
	        new_jewellery_job_card.category = self.category
	        new_jewellery_job_card.smith_warehouse = stage.smith_warehouse
	        new_jewellery_job_card.expected_execution_time = stage.expected_execution_time
	        new_jewellery_job_card.manufacturing_request = stage.manufacturing_stage
	        new_jewellery_job_card.stage = stage.manufacturing_stage
	        new_jewellery_job_card.supervisor_warehouse = self.supervisor_warehouse
	        new_jewellery_job_card.raw_material_from_previous_stage_only = stage.is_raw_material_from_previous_stage_only
	        new_jewellery_job_card.keep_metal_ledger = True
	        new_jewellery_job_card.flags.ignore_mandatory = True
	        new_jewellery_job_card.save(ignore_permissions=True)
	        frappe.db.set_value(stage.doctype, stage.name, 'job_card_created', 1)
	        if smith_email:
	            add_assignment({"doctype": "Jewellery Job Card", "name": new_jewellery_job_card.name, "smith": [smith_email]})
	        frappe.msgprint("Jewellery Job Card Orders Created.", indicator="green", alert=1)
	    else:
	        frappe.throw(_("Job card already exists for this stage"))
