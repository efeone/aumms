# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_link_to_form

from erpnext.stock.get_item_details import get_bin_details

from aumms.aumms.utils import (
	cancel_metal_ledger_entries,
	get_metal_balance_qty,
	repost_metal_ledger_balance,
)


class RawMaterialBundle(Document):
	def autoname(self):
		for items in self.get("items"):
			items.raw_material_id = f"{items.item}-{self.stage}-{items.required_weight}"

	def validate(self):
		self.set_row_warehouses()
		self.set_raw_material_available()

	def before_submit(self):
		self.validate_raw_material_available()

	def on_submit(self):
		self.mark_as_raw_material_bundle_created(created = 1)
		stock_entry = self.transfer_raw_materials_to_smith()
		# the ledger is posted at the moment the stock moved, so the two agree on a repost
		self.posting_date = stock_entry.posting_date
		self.posting_time = stock_entry.posting_time
		self.db_set({
			'stock_entry': stock_entry.name,
			'posting_date': self.posting_date,
			'posting_time': self.posting_time
		})
		self.create_metal_ledger_entries()

	def on_cancel(self):
		self.mark_as_raw_material_bundle_created(created = 0)
		self.cancel_stock_entry()
		cancel_metal_ledger_entries(self)

	def cancel_stock_entry(self):
		"""
			method to send the raw materials back from the smith to the source warehouse

			The metal ledger is reversed with the bundle, so the stock has to come back with
			it. A bundle whose materials the smith has already worked cannot be cancelled,
			and the Stock Entry says so itself.
		"""
		if not self.stock_entry:
			return
		stock_entry = frappe.get_doc('Stock Entry', self.stock_entry)
		if stock_entry.docstatus == 1:
			stock_entry.cancel()
			frappe.msgprint(
				msg = _('Stock Entry {0} is cancelled.').format(
					get_link_to_form('Stock Entry', stock_entry.name)
				),
				indicator = 'orange',
				alert = 1
			)

	def set_row_warehouses(self):
		"""
			method to point every raw material row at the source warehouse

			The whole bundle is picked from one warehouse, so a row is only asked for a
			warehouse of its own when it is picked from somewhere else.
		"""
		for item in self.items:
			if not item.warehouse:
				item.warehouse = self.source_warehouse

	def set_raw_material_available(self):
		"""
			method to flag whether the bundle can be picked in full

			A bundle is only available when every row is covered. One short row leaves the
			smith without a raw material, so the flag has to fall for the bundle as a whole.
		"""
		self.raw_material_available = 1 if self.items and all(
			flt(item.available_quantity) >= flt(item.required_quantity) for item in self.items
		) else 0

	def validate_raw_material_available(self):
		"""
			method to stop a bundle that cannot be picked from being submitted

			Submitting moves the stock to the smith. A short row would either fail deep inside
			the Stock Entry or drive the warehouse negative, so it is caught here by name.
		"""
		short_items = [
			item.item for item in self.items
			if flt(item.available_quantity) < flt(item.required_quantity)
		]
		if short_items:
			frappe.throw(
				_('Not enough stock in {0} for {1}. Create a Raw Material Request for the shortage first.').format(
					frappe.bold(self.source_warehouse), frappe.bold(', '.join(short_items))
				),
				title = _('Raw Material Not Available')
			)

	def get_manufacturing_stage_row(self):
		"""
			method to get the stage row of the Manufacturing Request this bundle is raised for
			output: dict of the smith and the warehouse they work out of, else None

			The bundle is raised against one stage, and the smith working that stage carries
			both the warehouse the metal goes to and the party it is then held against, so
			the stage row is the only place either can come from.
		"""
		if not self.manufacturing_stage:
			return None
		return frappe.db.get_value(
			'Manufacturing Request Stage', self.manufacturing_stage,
			['smith', 'smith_warehouse'], as_dict = 1
		)

	def transfer_raw_materials_to_smith(self):
		"""
			method to move the raw materials from the source warehouse to the smith
			output: the submitted Stock Entry doc
		"""
		if not self.source_warehouse:
			frappe.throw(_('Set Source Warehouse to transfer the raw materials.'))

		stage = self.get_manufacturing_stage_row()
		smith_warehouse = stage.smith_warehouse if stage else None
		if not smith_warehouse:
			frappe.throw(
				_('Set Smith Warehouse on the stage row of Manufacturing Request {0} to transfer the raw materials.').format(
					get_link_to_form('Manufacturing Request', self.manufacturing_request)
				)
			)

		stock_entry = frappe.new_doc('Stock Entry')
		stock_entry.stock_entry_type = 'Material Transfer'
		# purpose opens on the first of its options and is only fetched from the type after
		# validation has run, so it is set here rather than left to the fetch
		stock_entry.purpose = 'Material Transfer'
		stock_entry.company = frappe.defaults.get_defaults().company
		for item in self.items:
			stock_entry.append('items', {
				'item_code': item.item,
				's_warehouse': item.warehouse or self.source_warehouse,
				't_warehouse': smith_warehouse,
				'qty': item.required_quantity,
				'allow_zero_valuation_rate': 1
			})
		stock_entry.insert(ignore_permissions = True)
		stock_entry.submit()

		frappe.msgprint(
			msg = _('Stock Entry {0} is created.').format(
				get_link_to_form('Stock Entry', stock_entry.name)
			),
			indicator = 'green',
			alert = 1
		)
		return stock_entry

	def create_metal_ledger_entries(self):
		"""
			method to take the metal handed to the smith out of the metal ledger

			The metal ledger has no warehouse of its own, so a bundle is written as a single
			outgoing entry per row for the weight that left the source warehouse. Only the
			rows that are AuMMS Items are written, the stock of every row having already
			moved on the Stock Entry.
		"""
		company = frappe.defaults.get_defaults().company
		stage = self.get_manufacturing_stage_row()
		# the metal is out of the strong room but not spent, it is held against the smith
		smith = stage.smith if stage else None
		# series touched by this bundle, reposted once each after the entries are in
		metal_ledger_series = set()

		for item in self.items:
			# a raw material outside the metal masters, brass or copper say, moves in stock
			# but carries no purity, so there is no metal series for it to belong to
			if not frappe.db.exists('AuMMS Item', item.item):
				continue
			aumms_item_doc = frappe.get_doc('AuMMS Item', item.item)
			# the weight uom rides on the item, the bundle uom only stands in when it has none
			weight_uom = aumms_item_doc.weight_uom or self.uom
			if not weight_uom:
				frappe.throw(
					_('Set Weight UOM on Item {0} to keep a Metal Ledger for it.').format(
						get_link_to_form('AuMMS Item', aumms_item_doc.name)
					)
				)

			metal_qty = flt(item.required_weight)
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
				'company': company,
				'party_type': 'Smith' if smith else None,
				'party': smith,
				'item_code': item.item,
				'item_name': aumms_item_doc.item_name,
				'stock_uom': weight_uom,
				'item_type': aumms_item_doc.item_type,
				'purity': aumms_item_doc.purity,
				'purity_percentage': aumms_item_doc.purity_percentage,
				'in_qty': 0,
				'out_qty': metal_qty,
				'balance_qty': balance_qty - metal_qty
			}).insert(ignore_permissions = 1)
			metal_ledger_series.add((aumms_item_doc.item_type, aumms_item_doc.purity, weight_uom))

		# a back dated bundle lands before entries that are already posted, so their balance
		# is rewritten too. A bundle posted last of all walks only its own rows.
		for item_type, purity, stock_uom in metal_ledger_series:
			repost_metal_ledger_balance(
				item_type, purity, stock_uom, self.posting_date, self.posting_time
			)

		if metal_ledger_series:
			frappe.msgprint(
				msg = _('Metal Ledger Entry is created.'),
				indicator = 'green',
				alert = 1
			)

	def mark_as_raw_material_bundle_created(self, created):
		if frappe.db.exists('Manufacturing Request', self.manufacturing_request):
			manufacturing_request = frappe.get_doc('Manufacturing Request', self.manufacturing_request)
			if manufacturing_request:
				updated = False
				for stage in manufacturing_request.manufacturing_stages:
					if stage.manufacturing_stage == self.stage:
						stage.raw_material_bundle_created = created
						frappe.db.set_value('Manufacturing Request Stage', stage.name, 'raw_material_bundle_created', created)
						frappe.db.set_value('Manufacturing Request Stage', stage.name, 'raw_material_available', created)
						break
				# the metal going out to the smith is the first sign of the piece being made
				manufacturing_request.set_status()


@frappe.whitelist()
def get_available_stock(item, warehouse):
	"""
		method to get the stock a warehouse holds for a raw material
		args:
			item: item code of the raw material
			warehouse: warehouse the raw material is picked from
		output: dict of the quantity in stock and the metal weight it carries

		A raw material stocked by weight needs no conversion. One stocked by the piece
		carries its metal weight on the item master, so the pieces are multiplied by it.
	"""
	if not item or not warehouse:
		return {'available_quantity': 0, 'available_weight': 0}

	available_quantity = flt(get_bin_details(item, warehouse).get('actual_qty'))
	available_weight = available_quantity

	aumms_item = frappe.db.get_value(
		'AuMMS Item', item, ['stock_uom', 'weight_uom', 'gold_weight', 'weight_per_unit'], as_dict = 1
	)
	if aumms_item and aumms_item.weight_uom and aumms_item.stock_uom != aumms_item.weight_uom:
		# an item held in pieces carries no weight of its own until the item master is filled in
		weight_per_unit = flt(aumms_item.gold_weight) or flt(aumms_item.weight_per_unit)
		available_weight = available_quantity * weight_per_unit

	return {'available_quantity': available_quantity, 'available_weight': available_weight}


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
    frappe.msgprint(f"{raw_material_request_count} Raw Material Request Created.", indicator="green", alert=True)
