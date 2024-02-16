# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.model.mapper import get_mapped_doc

class PurchaseTool(Document):

    def autoname(self):
        """
        Set the autoname for the document based on the specified format.
        """
        if self.has_stone:
            # If the item has a stone, use the specified format
            for item_detail in self.get("item_details"):
                item_detail.item_code = f"{self.item_category} {item_detail.stone_weight} {item_detail.stone} {item_detail.gold_weight}"
        else:
            # If there is no stone, use a different format
            for item_detail in self.get("item_details"):
                item_detail.item_code = f"{self.item_category} {item_detail.gold_weight}"


    def before_submit(self):
        self.create_item()

    def on_submit(self):
        self.create_purchase_receipt()

    def create_item(self):
        for item_detail in self.get("item_details"):
            aumms_item = frappe.new_doc('AuMMS Item')
            aumms_item.item_code = item_detail.item_code
            aumms_item.item_name = item_detail.item_code
            aumms_item.purity = item_detail.purity
            aumms_item.item_group = self.item_group
            aumms_item.item_type = self.item_type
            aumms_item.weight_per_unit = item_detail.net_weight
            aumms_item.weight_uom = item_detail.uom
            aumms_item.has_stone = self.has_stone
            # If has_stone is checked, fetch stone details from item_detail
            if self.has_stone:
                aumms_item.append('stone_details', {
                    'stone_weight': item_detail.stone_weight,
                    'stone_charge': item_detail.stone_charge,
                    'item_name': self.stone,
                    'item_type': self.stone,
                })
            frappe.msgprint('AuMMS Item Created.')
            aumms_item.insert(ignore_permissions=True)

    def create_purchase_receipt(self):
        purchase_receipt = frappe.new_doc('Purchase Receipt')
        purchase_receipt.supplier = self.supplier,
        purchase_receipt.keep_metal_ledger = 1

        for item_detail in self.get("item_details"):
            # Fetch details from AuMMS Item's item_details
            aumms_item = frappe.get_doc('AuMMS Item', item_detail.item_code)

            purchase_receipt.append('items', {
                'item_code': aumms_item.item_code,
                'item_name': aumms_item.item_name,
                'qty': item_detail.net_weight,
                'uom': item_detail.uom,
                'stock_uom': aumms_item.weight_uom,
                'conversion_factor': aumms_item.weight_per_unit / item_detail.net_weight,
                'base_rate': self.board_rate,
            })

            # Save and submit the Purchase Receipt
            purchase_receipt.insert(ignore_permissions=True)
            purchase_receipt.save(ignore_permissions=True)
            purchase_receipt.submit()

            frappe.msgprint('Purchase Receipt created and submitted successfully.')
