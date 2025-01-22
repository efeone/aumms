import frappe
from frappe.model.document import Document

class JewelleryReceipt(Document):

	def autoname(self):
		"""
		Set the autoname for the document based on the specified format.
		"""
		for item_detail in self.get("item_details"):
			item_code_parts = [self.item_category, str(item_detail.gold_weight)]

			if item_detail.has_stone:
				for stone in self.item_wise_stone_details:
					if stone.reference == item_detail.idx:
						item_code_parts.append(stone.stone)		

			item_detail.item_code = ' '.join(item_code_parts)

	def validate(self):
		self.validate_date()
  
	def before_save(self):
		total_gold_weight = 0
		for item in self.item_details:
			total_gold_weight += item.gold_weight
		self.total_gold_weight = total_gold_weight

	def on_submit(self):
		self.create_item()
		self.create_purchase_receipt()
		self.make_form_read_only(['aumms_item', 'purchase_receipt', 'metal_ledger'])

	def validate_date(self):
		self.calculate_item_details()

	def make_form_read_only(self, fields):
		for field in fields:
			self.set(field, 'read_only', 1)

	def create_item(self):
		for item_detail in self.get("item_details"):
			aumms_item = frappe.new_doc('AuMMS Item')
			aumms_item.item_code = item_detail.item_code
			aumms_item.item_name = item_detail.item_code
			aumms_item.purity = self.purity
			aumms_item.item_group = self.item_group
			aumms_item.item_type = self.item_type
			aumms_item.weight_per_unit = item_detail.net_weight
			aumms_item.weight_uom = item_detail.uom
			aumms_item.has_stone = item_detail.has_stone
			aumms_item.gold_weight = item_detail.gold_weight
			aumms_item.item_category = item_detail.item_category
			aumms_item.is_purchase_item = 1
			aumms_item.is_sales_item = 1 if item_detail.is_sales_item else 0

			if item_detail.hallmarked:
				aumms_item.hallmarked = 1
				aumms_item.huid = item_detail.huid

			# Add only the relevant stone details based on the reference
			if item_detail.has_stone:
				for stone in self.item_wise_stone_details:
					if stone.reference == item_detail.idx: 
						aumms_item.append("stone_details", {
							"stone_weight": stone.stone_weight,
							"stone_charge": stone.rate * stone.stone_weight,
							"item_name": stone.stone,
							"stone_type": stone.stone
						})

			aumms_item.insert(ignore_permissions=True)
			frappe.msgprint('AuMMS Item Created.', indicator="green", alert=1)

	def create_purchase_receipt(self):
		purchase_receipt = frappe.new_doc('Purchase Receipt')
		purchase_receipt.supplier = self.supplier
		purchase_receipt.keep_metal_ledger = 1

		for item_detail in self.get("item_details"):
			purchase_receipt.append('items', {
				'item_code': item_detail.item_code,
				'item_name': item_detail.item_code,
				'board_rate': self.board_rate or 0,
				'qty': 1,
				'uom': "Nos",
				"weight_per_unit": item_detail.gold_weight,
				"weight_uom": item_detail.uom,
				'base_rate': item_detail.amount,
				'rate': item_detail.amount,
				'making_charge': item_detail.making_charge or 0,
				'stone_weight': item_detail.stone_weight or 0,
				'stone_charge': item_detail.stone_charge or 0,
			})
		purchase_receipt.insert(ignore_permissions=True)
		purchase_receipt.submit()
		frappe.msgprint('Purchase Receipt created.', indicator="green", alert=1)

	@frappe.whitelist()
	def calculate_item_details(self):
		for item_detail in self.get("item_details"):
			board_rate = self.board_rate or 0
			stone_charge = item_detail.stone_charge or 0
			gold_weight = item_detail.gold_weight or 0
			making_chargein_percentage = item_detail.making_chargein_percentage or 0

			if item_detail.has_stone:
				item_detail.amount_without_making_charge = (gold_weight * board_rate) + stone_charge
			else:
				item_detail.amount_without_making_charge = gold_weight * board_rate

			item_detail.making_charge = item_detail.amount_without_making_charge * (making_chargein_percentage / 100)
			item_detail.amount = item_detail.amount_without_making_charge + item_detail.making_charge
