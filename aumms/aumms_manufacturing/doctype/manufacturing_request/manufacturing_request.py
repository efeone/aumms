# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.desk.form.assign_to import add as add_assignment
from frappe.utils import flt, get_link_to_form, time_diff_in_hours

from aumms.aumms.utils import (
	cancel_metal_ledger_entries,
	create_notification_log,
	get_metal_balance_qty,
	repost_metal_ledger_balance,
)

class ManufacturingRequest(Document):

	def autoname(self):
		if self.request_from == "Jewellery Order":
			self.title = f"{self.purity}  {self.expected_weight} {self.uom}  {self.type}  {self.category}"
		elif self.request_from == "Raw Material Request" :
			self.title = f"{self.purity}  {self.expected_weight} {self.uom}  {self.type}"

	def before_insert(self):
		self.update_manufacturing_stages()

	def before_submit(self):
		self.send_notification_to_owner()

	def on_update_after_submit(self):
		self.mark_as_finished()

	def on_submit(self):
		self.mark_as_finished_in_jewellery_order()
		self.manufacturing_request_finished(finished = 1)
		self.manufacture_finished_good()

	def on_cancel(self):
		self.manufacturing_request_finished(finished = 0)
		self.cancel_stock_entries()
		cancel_metal_ledger_entries(self)

	def get_last_stage(self):
		"""
			method to get the stage row that finishes the piece
			output: the last Manufacturing Request Stage row, else None

			The stages run in grid order and the metal is handed on from one smith to the
			next, so it is the last of them who holds the finished piece.
		"""
		return self.manufacturing_stages[-1] if self.manufacturing_stages else None

	def get_smith_warehouse(self):
		"""
			method to get the warehouse the finished piece is made in and bought back from
		"""
		last_stage = self.get_last_stage()
		smith_warehouse = last_stage.smith_warehouse if last_stage else None
		if not smith_warehouse:
			frappe.throw(
				_('Set Smith Warehouse on the last stage of {0} to move the finished goods.').format(
					frappe.bold(self.name)
				)
			)
		return smith_warehouse

	def manufacture_finished_good(self):
		"""
			method to turn the raw materials held by the smith into the finished piece

			The raw materials were transferred to the smith and are still on his books. A
			plain receipt of the piece would leave them there and count the same metal twice,
			so the two legs are written as one Manufacture entry.
		"""
		if not self.product:
			frappe.throw(
				_('No product on {0}. Submit the last stage job card first, it is what names the finished item.').format(
					frappe.bold(self.name)
				)
			)

		smith_warehouse = self.get_smith_warehouse()
		raw_materials = self.get_raw_materials_consumed()
		if not raw_materials:
			frappe.throw(
				_('No submitted Raw Material Bundle for {0}, so there is nothing for the piece to be made of.').format(
					frappe.bold(self.name)
				)
			)

		stock_entry = frappe.new_doc('Stock Entry')
		stock_entry.stock_entry_type = 'Manufacture'
		# purpose opens on the first of its options and is only fetched from the type after
		# validation has run, so it is set here or the entry is validated as a Material Issue
		stock_entry.purpose = 'Manufacture'
		stock_entry.company = frappe.defaults.get_defaults().company

		for raw_material in raw_materials:
			stock_entry.append('items', {
				'item_code': raw_material.item,
				's_warehouse': raw_material.warehouse,
				'qty': raw_material.required_quantity,
				'allow_zero_valuation_rate': 1
			})

		# an independent Manufacture entry is never auto flagged, the finished row says so itself
		stock_entry.append('items', {
			'item_code': self.product,
			't_warehouse': smith_warehouse,
			'qty': self.quantity or 1,
			'is_finished_item': 1
		})

		stock_entry.insert(ignore_permissions = True)
		stock_entry.submit()

		self.db_set({
			'manufacture_stock_entry': stock_entry.name,
			'posting_date': stock_entry.posting_date,
			'posting_time': stock_entry.posting_time
		})
		frappe.msgprint(
			msg = _('Stock Entry {0} is created.').format(
				get_link_to_form('Stock Entry', stock_entry.name)
			),
			indicator = 'green',
			alert = 1
		)

	def get_raw_materials_consumed(self):
		"""
			method to get the raw materials the smiths were issued for this request
			output: list of dicts of the item, the warehouse holding it and the quantity

			A bundle row names the warehouse the material was picked from, which is where it
			no longer is. The bundle moved it on to the smith of the stage it was raised
			against, so that is the warehouse it is consumed out of. A bundle is raised per
			stage, and each stage has its own smith, so the warehouse is resolved per bundle
			rather than one standing for the whole request.
		"""
		bundles = frappe.get_all(
			'Raw Material Bundle',
			filters = {'manufacturing_request': self.name, 'docstatus': 1},
			fields = ['name', 'manufacturing_stage']
		)

		raw_materials = []
		for bundle in bundles:
			smith_warehouse = frappe.db.get_value(
				'Manufacturing Request Stage', bundle.manufacturing_stage, 'smith_warehouse'
			)
			if not smith_warehouse:
				frappe.throw(
					_('No Smith Warehouse on the stage of {0}, so its raw materials cannot be traced.').format(
						get_link_to_form('Raw Material Bundle', bundle.name)
					)
				)
			for row in frappe.get_all(
				'Raw Material Details',
				filters = {'parent': bundle.name, 'parenttype': 'Raw Material Bundle'},
				fields = ['item', 'required_quantity']
			):
				raw_materials.append(frappe._dict({
					'item': row.item,
					'warehouse': smith_warehouse,
					'required_quantity': row.required_quantity
				}))
		return raw_materials

	@frappe.whitelist()
	def buy_back_finished_good(self):
		"""
			method to take the finished piece back from the smith into the store

			The metal left the ledger when the raw material went out to the smith. It comes
			back in as the finished piece, so the ledger is written inbound against the same
			smith and the balance closes.
		"""
		if self.buy_back_stock_entry:
			frappe.throw(
				_('Finished goods are already bought back on {0}.').format(
					get_link_to_form('Stock Entry', self.buy_back_stock_entry)
				)
			)
		if not self.supervisor_warehouse:
			frappe.throw(_('Set Supervisor Warehouse to buy the finished goods back.'))

		smith_warehouse = self.get_smith_warehouse()

		stock_entry = frappe.new_doc('Stock Entry')
		stock_entry.stock_entry_type = 'Material Transfer'
		stock_entry.purpose = 'Material Transfer'
		stock_entry.company = frappe.defaults.get_defaults().company
		stock_entry.append('items', {
			'item_code': self.product,
			's_warehouse': smith_warehouse,
			't_warehouse': self.supervisor_warehouse,
			'qty': self.quantity or 1,
			'allow_zero_valuation_rate': 1
		})
		stock_entry.insert(ignore_permissions = True)
		stock_entry.submit()

		self.db_set({
			'buy_back_stock_entry': stock_entry.name,
			'posting_date': stock_entry.posting_date,
			'posting_time': stock_entry.posting_time
		})
		self.create_metal_ledger_entry()

		frappe.msgprint(
			msg = _('Stock Entry {0} is created.').format(
				get_link_to_form('Stock Entry', stock_entry.name)
			),
			indicator = 'green',
			alert = 1
		)
		return stock_entry.name

	def create_metal_ledger_entry(self):
		"""
			method to bring the metal of the finished piece back into the metal ledger
		"""
		if not frappe.db.exists('AuMMS Item', self.product):
			frappe.throw(
				_('Item {0} has no AuMMS Item, so its purity and type cannot be posted to the Metal Ledger.').format(
					frappe.bold(self.product)
				)
			)
		aumms_item_doc = frappe.get_doc('AuMMS Item', self.product)

		weight_uom = aumms_item_doc.weight_uom or self.weight_uom
		if not weight_uom:
			frappe.throw(
				_('Set Weight UOM on Item {0} to keep a Metal Ledger for it.').format(
					get_link_to_form('AuMMS Item', aumms_item_doc.name)
				)
			)

		# the piece is weighed off the item master, the request weight only stands in for it
		metal_qty = flt(aumms_item_doc.gold_weight) * flt(self.quantity or 1) or flt(self.weight)
		last_stage = self.get_last_stage()
		smith = last_stage.smith if last_stage else None

		balance_qty = get_metal_balance_qty(
			aumms_item_doc.item_type, aumms_item_doc.purity, weight_uom,
			self.posting_date, self.posting_time
		)
		frappe.get_doc({
			'doctype': 'Metal Ledger Entry',
			'posting_date': self.posting_date,
			'posting_time': self.posting_time,
			'voucher_type': self.doctype,
			'voucher_no': self.name,
			'company': frappe.defaults.get_defaults().company,
			'party_type': 'Smith' if smith else None,
			'party': smith,
			'item_code': self.product,
			'item_name': aumms_item_doc.item_name,
			'stock_uom': weight_uom,
			'item_type': aumms_item_doc.item_type,
			'purity': aumms_item_doc.purity,
			'purity_percentage': aumms_item_doc.purity_percentage,
			'in_qty': metal_qty,
			'out_qty': 0,
			'balance_qty': balance_qty + metal_qty
		}).insert(ignore_permissions = 1)

		repost_metal_ledger_balance(
			aumms_item_doc.item_type, aumms_item_doc.purity, weight_uom,
			self.posting_date, self.posting_time
		)
		frappe.msgprint(
			msg = _('Metal Ledger Entry is created.'),
			indicator = 'green',
			alert = 1
		)

	def cancel_stock_entries(self):
		"""
			method to unwind the stock this request moved

			The buy back is undone before the manufacture, or the piece would be cancelled
			out of the smith's warehouse while the store still holds it.
		"""
		for fieldname in ('buy_back_stock_entry', 'manufacture_stock_entry'):
			stock_entry_name = self.get(fieldname)
			if not stock_entry_name:
				continue
			stock_entry = frappe.get_doc('Stock Entry', stock_entry_name)
			if stock_entry.docstatus == 1:
				stock_entry.cancel()
				frappe.msgprint(
					msg = _('Stock Entry {0} is cancelled.').format(
						get_link_to_form('Stock Entry', stock_entry.name)
					),
					indicator = 'orange',
					alert = 1
				)

	def update_manufacturing_stages(self):
		if self.category:
			category_doc = frappe.get_doc('Item Category', self.category)
			for stage in category_doc.stages:
				self.append('manufacturing_stages', {
					'manufacturing_stage': stage.stage,
					'expected_execution_time': stage.required_time,
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
	def update_previous_stage_weight(self, idx):
		for stage in self.manufacturing_stages:
			if stage.idx == idx:
				if stage.previous_stage_completed:
					prev_row = stage.idx - 1
					for row in self.manufacturing_stages:
						if row.idx == prev_row:
							return row.weight

	@frappe.whitelist()
	def create_jewellery_job_card(self, stage_row_id):
		first_stage, last_stage = False, False
		if self.manufacturing_stages:
			first_stage = self.manufacturing_stages[0].name
			last_stage = self.manufacturing_stages[-1].name
		stage = frappe.get_doc('Manufacturing Request Stage', stage_row_id)
		jewellery_job_card_exists = frappe.db.exists('Jewellery Job Card', {
			'manufacturing_request': self.name,
			'manufacturing_stage': stage.manufacturing_stage
		})

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
			new_jewellery_job_card.manufacturing_stage = stage.manufacturing_stage
			new_jewellery_job_card.stage = stage.manufacturing_stage
			new_jewellery_job_card.supervisor_warehouse = self.supervisor_warehouse
			new_jewellery_job_card.raw_material_from_previous_stage_only = stage.is_raw_material_from_previous_stage_only
			new_jewellery_job_card.keep_metal_ledger = 1
			if first_stage == stage_row_id:
				new_jewellery_job_card.is_first_stage = 1
			if last_stage == stage_row_id:
				new_jewellery_job_card.is_last_stage = 1
			new_jewellery_job_card.flags.ignore_mandatory = True
			new_jewellery_job_card.save(ignore_permissions=True)
			frappe.db.set_value('Jewellery Job Card', self.manufacturing_request, 'product',self.product)
			frappe.db.set_value(stage.doctype, stage.name, 'job_card_created', 1)
			if smith_email:
				add_assignment({
					"doctype": new_jewellery_job_card.doctype,
					"name": new_jewellery_job_card.name,
					"assign_to": [smith_email]
				})
			frappe.msgprint("Jewellery Job Card Created.", indicator="green", alert=1)
		else:
			frappe.throw(_("Job card already exists for this stage"))


@frappe.whitelist()
def get_smith_payable(manufacturing_request, smith):
	"""
		method to work out what a smith is owed for a manufacturing request
		args:
			manufacturing_request: name of the Manufacturing Request
			smith: name of the Smith who did the work
		output: dict of the hours worked, the hourly rate and the amount they come to

		The hours are added up from the start and end times rather than read off the job
		card, the duration there being written by the browser. Nothing else in the app
		prices a smith's work, so this stands as a suggestion and not as the charge.
	"""
	job_cards = frappe.get_all(
		'Jewellery Job Card',
		filters = {
			'manufacturing_request': manufacturing_request,
			'smith': smith,
			'docstatus': 1
		},
		pluck = 'name'
	)

	hours = 0
	for job_card in job_cards:
		for row in frappe.get_all(
			'Job Time',
			filters = {'parent': job_card, 'parenttype': 'Jewellery Job Card'},
			fields = ['start_time', 'end_time']
		):
			if row.start_time and row.end_time:
				hours += time_diff_in_hours(row.end_time, row.start_time)

	hourly_rate = flt(frappe.db.get_value('Smith', smith, 'hourly_rate'))
	return {
		'hours': hours,
		'hourly_rate': hourly_rate,
		'payable_amount': flt(hours * hourly_rate, 2)
	}
