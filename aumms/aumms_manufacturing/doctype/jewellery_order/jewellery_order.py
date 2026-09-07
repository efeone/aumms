# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import flt

class JewelleryOrder(Document):
	def validate(self):
		self.calculate_available_item_totals()

	def on_submit(self):
		self.create_manufacturing_request()
		self.jewellery_order_finished(finished = 1)
		self.validate_jewellery_order_items()

	def on_cancel(self):
		self.jewellery_order_finished(finished = 0)

	def on_update(self):
		self.out_for_delivery_check()

	def before_insert(self):
		self.update_jewellery_order_items()

	def autoname(self):
		if self.order_from == "Customer Jewellery Order":
			naming_series ='JO-CJO-' + '.####'
			self.name = make_autoname(naming_series)
		elif self.order_from == "Jewellery Stock Request":
			naming_series ='JO-JSR-' + '.####'
			self.name = make_autoname(naming_series)

	def calculate_available_item_totals(self):
		"""
			method to total the weight of the order and of the items already in stock

			The totals are read off the rows rather than keyed in, so they are worked out here
			and not on the desk. A form that recomputed them on every reload would go dirty
			without the user having touched it.
		"""
		available_items = [item for item in self.jewellery_order_items if item.is_available]
		self.total_weight = sum(flt(item.weight) for item in self.jewellery_order_items)
		self.weight_of_available_item = sum(flt(item.weight) for item in available_items)
		self.available_item_quantity = len(available_items)

	def update_jewellery_order_items(self):
		if self.docstatus == 0:
			current_rows = len(self.jewellery_order_items)
			required_rows = self.quantity
			rows_to_add = required_rows - current_rows
			if rows_to_add > 0:
				for _ in range(rows_to_add):
					self.append('jewellery_order_items', {
						'item': '',
						'weight': self.expected_total_weight / self.quantity
					})
			elif rows_to_add < 0:
				self.jewellery_order_items = self.jewellery_order_items[:required_rows]
		if not self.jewellery_order_items:
			frappe.throw(_("Jewellery Order Items table is Mandatory."))

	def validate_jewellery_order_items(self):
		if len(self.jewellery_order_items) == 0:
			frappe.throw(_("The Jewellery Order Items table cannot be empty."))

	def create_manufacturing_request(self):
		"""Create Manufacturing Request For Jewellery Order"""
		manufacturing_request_exists = frappe.db.exists('Manufacturing Request', {"jewellery_order": self.name})
		warehouse = frappe.get_single("AuMMS Settings").get("default_warehouse")
		if not warehouse:
			frappe.throw(_("Please Set the Smith Warehouse in AuMMS Settings"))
		if not manufacturing_request_exists:
			manufacturing_request_count = 0
			for item in self.jewellery_order_items:
				if item.is_available == 0:
					new_manufacturing_request = frappe.new_doc('Manufacturing Request')
					new_manufacturing_request.request_from = "Jewellery Order"
					new_manufacturing_request.jewellery_order = self.name
					new_manufacturing_request.design = self.design
					new_manufacturing_request.required_date = self.required_date
					new_manufacturing_request.uom = self.uom
					new_manufacturing_request.weight_uom = self.weight_uom
					new_manufacturing_request.expected_weight = item.weight
					new_manufacturing_request.purity = self.purity
					new_manufacturing_request.type = self.type
					new_manufacturing_request.quantity = 1
					new_manufacturing_request.category = self.category
					new_manufacturing_request.design_description = self.design_description
					new_manufacturing_request.keep_metal_ledger = True
					new_manufacturing_request.jewellery_order_item = item.name
					new_manufacturing_request.supervisor_warehouse = warehouse
					new_manufacturing_request.insert(ignore_permissions=True)
					manufacturing_request_count += 1
					frappe.db.set_value(item.doctype, item.name, 'requested_for_manufacturing', 1)
			frappe.msgprint(f"{manufacturing_request_count} Manufacturing Request Created.", indicator="green", alert=1)

		else:
			frappe.throw(_('Manufacturing request for Jewellery Order {0} already exists'.format(self.name)))


	def out_for_delivery_check(self):
		if frappe.db.exists('Customer Jewellery Order', {'name': self.customer_jewellery_order, 'out_for_delivery': 0}):
			customer_jewellery_order = frappe.get_doc('Customer Jewellery Order', self.customer_jewellery_order)
			if customer_jewellery_order:
				jewellery_order_list = frappe.db.sql("""
					SELECT
						name,
						finished
					FROM
						`tabJewellery Order`
					WHERE
						customer_jewellery_order = %s
				""", (self.customer_jewellery_order,), as_dict=True)

				all_finished = all(jewellery_order['finished'] == 1 for jewellery_order in jewellery_order_list)
				if all_finished:
					frappe.db.set_value('Customer Jewellery Order', self.customer_jewellery_order, 'out_for_delivery', 1)
				else:
					frappe.db.set_value('Customer Jewellery Order', self.customer_jewellery_order, 'out_for_delivery', 0)

	def jewellery_order_finished(self, finished):
		if frappe.db.exists('Customer Jewellery Order', self.customer_jewellery_order):
			customer_jewellery_order = frappe.get_doc('Customer Jewellery Order', self.customer_jewellery_order)
			if customer_jewellery_order:
				updated = False
				for item in customer_jewellery_order.order_items:
					if item.item_category == self.category:
						item.jewellery_order_finished = finished
						frappe.db.set_value('Customer Jewellery Order Detail', item.name, 'jewellery_order_finished',finished)
						break
