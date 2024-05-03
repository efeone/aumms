# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document

class JewelleryJobCard(Document):
    def before_insert(self):
        self.update_item_table()

    def on_submit(self):
        self.mark_as_completed(completed=1)
        self.create_metal_ledger()

    def on_cancel(self):
        self.mark_as_completed(completed=0)

    def validate(self):
        self.create_metal_ledger()

    def update_item_table(self):
        if frappe.db.exists('Raw Material Bundle', {'manufacturing_request': self.manufacturing_request}):
            raw_material_doc = frappe.get_doc('Raw Material Bundle', {'manufacturing_request': self.manufacturing_request})
            for item in raw_material_doc.items:
                self.append('item_details', {
                    'item': item.item,
                    # 'raw_material_id' : item.raw_material_id,
                    # 'item_type': item.item_type,
                    'quantity': item.required_quantity,
                    'weight':item.required_weight
                })

    def mark_as_completed(self, completed):
        if frappe.db.exists('Manufacturing Request', self.manufacturing_request):
            manufacturing_request = frappe.get_doc('Manufacturing Request', self.manufacturing_request)
            if manufacturing_request:
                updated = False
                for stage in manufacturing_request.manufacturing_stages:
                    if stage.manufacturing_stage == self.manufacturing_stage:
                        stage.completed = completed
                        frappe.db.set_value('Manufacturing  Stage', stage.name, 'completed', completed)
                        manufacturing_request.mark_as_finished()
                        break

    def create_metal_ledger(self) :
        if self.keep_metal_ledger:
            # if frappe.db.exists('Metal Ledger Entry',{'voucher_type': self.doctype, 'voucher_no': self.name}):
            for item in self.item_details:
                new_metal_ledger = frappe.new_doc('Metal Ledger Entry')
                new_metal_ledger.posting_date = frappe.utils.today()
                new_metal_ledger.posting_time = frappe.utils.now()
                new_metal_ledger.voucher_type = self.doctype
                new_metal_ledger.voucher_no = self.name
                # new_metal_ledger.party_link = self.party_link
                new_metal_ledger.item_code = item.item
                new_metal_ledger.item_name = item.item
                new_metal_ledger.stock_uom = self.uom
                new_metal_ledger.item_type = self.type
                new_metal_ledger.purity = self.purity
                new_metal_ledger.out_qty = self.quantity
                new_metal_ledger.balance_qty = 0
                new_metal_ledger.insert(ignore_permissions=True)
                frappe.msgprint("Metal Ledger Created.", indicator="green", alert=1)
