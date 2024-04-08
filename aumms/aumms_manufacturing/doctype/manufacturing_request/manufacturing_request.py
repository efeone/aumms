# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt
import frappe
from frappe import _
from frappe.model.document import Document
from aumms.aumms.utils import create_notification_log
from frappe.desk.form.assign_to import add as add_assignment

class ManufacturingRequest(Document):

	def before_insert(self):
		self.update_manufacturing_stages()

	def before_submit(self):
		self.send_notification_to_owner()

	def update_manufacturing_stages(self):
		if self.category:
			category_doc = frappe.get_doc('Item Category', self.category)
			for stage in category_doc.stages:
				self.append('manufacturing_request_stage', {
					'manufacturing_stage': stage.stage,
					'required_time': stage.required_time,
					'workstation': stage.default_workstation
				})


	def send_notification_to_owner(self):
		for manufacturing_request in self.manufacturing_request_stage:
			if manufacturing_request.assigned_to:
				subject = "Manufacturing Stage Assigned"
				content = f"Manufacturing Stage {manufacturing_request.manufacturing_stage} is Assigned to {manufacturing_request.assigned_to}"
				for_user = self.owner
				create_notification_log(self.doctype, self.name, for_user, subject, content, 'Alert')


	@frappe.whitelist()
	def update_previous_stage(self, idx):
		for stage in self.manufacturing_request_stage:
			if stage.idx == idx:
				if stage.awaiting_raw_material:
					prev_row = stage.idx - 1
					for row in self.manufacturing_request_stage:
						if row.idx == prev_row:
							return row.manufacturing_stage

	@frappe.whitelist()
	def create_jewellery_job_card(self, stage_row_id):
		stage = frappe.get_doc('Manufacturing Request Stage', stage_row_id)
		jewellery_job_card_exists = frappe.db.exists('Jewellery Job Card', {'manufacturing_request': self.manufacturing_request,'manufacturing_stage': stage.manufacturing_stage })
		if not jewellery_job_card_exists:
			smith_email = frappe.db.get_value('Smith', stage.assigned_to, 'email')
			new_jewellery_job_card = frappe.new_doc('Jewellery Job Card')
			new_jewellery_job_card.manufacturing_request = self.name
			new_jewellery_job_card.assign_to = stage.assigned_to
			new_jewellery_job_card.work_station = stage.workstation
			new_jewellery_job_card.manufacturing_stage = stage.manufacturing_stage
			new_jewellery_job_card.flags.ignore_mandatory = True
			new_jewellery_job_card.save(ignore_permissions=True)
			if smith_email:
				add_assignment({"doctype": "Jewellery Job Card", "name": new_jewellery_job_card.name, "assign_to": [smith_email]})
			frappe.msgprint("Jewellery Job Card Orders Created.", indicator="green", alert=1)
