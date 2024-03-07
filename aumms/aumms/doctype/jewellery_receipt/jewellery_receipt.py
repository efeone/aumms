# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt
import frappe
from frappe.model import meta
from frappe.utils import today
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.model.mapper import get_mapped_doc

class JewelleryReceipt(Document):

    def autoname(self):
        """
        Set the autoname for the document based on the specified format.
        """
        for item_detail in self.get("item_details"):
            item_code_parts = [self.item_category, str(item_detail.gold_weight)]

            if item_detail.has_stone:
                if item_detail.single_stone:
                    item_code_parts.extend([item_detail.stone, str(item_detail.stone_weight)])
                elif item_detail.multi_stone:
                    stones = item_detail.stones.split(',') if item_detail.stones else []
                    for stone in stones:
                        item_code_parts.append(stone)

            item_detail.item_code = ' '.join(item_code_parts)

    def validate(self):
        self.validate_date()

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

            # If has_stone is checked, fetch stone details from item_detail
            if item_detail.has_stone:
                if item_detail.single_stone:
                    aumms_item.append('stone_details', {
                        'stone_weight': item_detail.stone_weight,
                        'stone_charge': item_detail.stone_charge,
                        'item_name': item_detail.stone,
                        'stone_type': item_detail.stone,
                    })
                else:
                    stones = item_detail.stones.split(',') if item_detail.stones else []
                    individual_stone_weight = item_detail.individual_stone_weight
                    if individual_stone_weight:
                        stone_weight = individual_stone_weight.split(',')
                        for stone, weight in zip(stones, stone_weight):
                            aumms_item.append('stone_details', {
                                'stone_weight': float(weight),
                                'stone_charge': item_detail.unit_stone_charge * float(weight),
                                'item_name': stone,
                                'stone_type': stone,
                            })

            aumms_item.insert(ignore_permissions=True)
            frappe.msgprint('AuMMS Item Created.', indicator="green", alert=1)

            # Fetch the item_code of the created AuMMS Item
            created_item_code = aumms_item.item_code

            # Use the fetched item_code for further processing
            # For example, you might need to store this item_code in the original document for reference


    def create_purchase_receipt(self):
            # Create a new Purchase Receipt
            purchase_receipt = frappe.new_doc('Purchase Receipt')
            purchase_receipt.supplier = self.supplier
            # purchase_receipt.total_qty = self.quantity
            purchase_receipt.keep_metal_ledger = 1

            for item_detail in self.get("item_details"):
                purchase_receipt.append('items', {
                    'item_code': item_detail.item_code,
                    'item_name': item_detail.item_code,
                    'board_rate': self.board_rate,
                    'qty': item_detail.gold_weight,
                    'uom': item_detail.uom,
                    'stock_uom': item_detail.uom,
                    'conversion_factor': 1,
                    'base_rate': self.board_rate,
                    'rate': item_detail.amount / item_detail.gold_weight,
                    'custom_making_charge': item_detail.making_charge,
                    'custom_stone_weight': item_detail.stone_weight,
                    'custom_stone_charge': item_detail.stone_charge,

                })
            # Insert the new document
            purchase_receipt.insert(ignore_permissions=True)

            # Submit the Purchase Receipt
            purchase_receipt.submit()
            frappe.msgprint('Purchase Receipt created.', indicator="green", alert=1)

        # except frappe.DuplicateEntryError as e:
        #     # Handle duplicate entry error
        #     frappe.msgprint(f'Duplicate entry error: {e}', indicator="red", alert=1)
        # except Exception as ex:
        #     # Handle other exceptions
        #     frappe.msgprint(f'Error: {ex}', indicator="red", alert=1)

    def calculate_item_details(self):
        for item_detail in self.get("item_details"):
            if item_detail.has_stone:
                if item_detail.stone_weight:
                    item_detail.net_weight = item_detail.gold_weight + item_detail.stone_weight
                    if item_detail.unit_stone_charge:
                        item_detail.stone_charge = item_detail.unit_stone_charge * item_detail.stone_weight
            else:
                item_detail.net_weight = item_detail.gold_weight
            if self.board_rate:
                if item_detail.has_stone:
                    item_detail.amount_without_making_charge = (item_detail.gold_weight * self.board_rate) + item_detail.stone_charge
                else:
                    item_detail.amount_without_making_charge = item_detail.gold_weight * self.board_rate

                if item_detail.amount_without_making_charge:
                    item_detail.making_charge = item_detail.amount_without_making_charge * (item_detail.making_chargein_percentage / 100)

                if item_detail.making_charge:
                    item_detail.amount = item_detail.amount_without_making_charge + item_detail.making_charge
            frappe.db.commit()
