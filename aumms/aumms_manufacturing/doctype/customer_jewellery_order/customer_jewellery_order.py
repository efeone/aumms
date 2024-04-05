# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CustomerJewelleryOrder(Document):

    def on_submit(self):
        self.create_jewellery_order()

    def create_jewellery_order(self):
        jewellery_order_exist = frappe.db.exists(
            "Jewellery Order", {"customer_jewellery_order": self.name}
        )
        if not jewellery_order_exist:
            jewellery_order_count = 0
            for item in self.order_item:
                new_jewellery_order = frappe.new_doc("Jewellery Order")
                new_jewellery_order.order_from = "Customer Jewellery Order"
                new_jewellery_order.customer_jewellery_order = self.name
                new_jewellery_order.order_item = f"{item.item_category}-{item.item_type}-{item.qty}"
                new_jewellery_order.required_date = self.required_date
                new_jewellery_order.uom = item.stock_uom
                new_jewellery_order.expected_total_weight = (
                    item.expected_weight_per_quantity
                )
                latest_board_rate = frappe.get_last_doc(
                    "Board Rate", {"purity": self.purity, "uom": "Gram"}
                )
                board_rate_value = latest_board_rate.board_rate
                new_jewellery_order.purity = self.purity
                new_jewellery_order.category = item.item_category
                new_jewellery_order.design = item.design
                new_jewellery_order.design_description = item.item_design_description
                new_jewellery_order.type = item.item_type
                new_jewellery_order.quantity = item.qty
                new_jewellery_order.expected_weight_per_quantity = (
                    item.expected_weight_per_quantity
                )
                new_jewellery_order.insert(ignore_permissions=True)
                item.jewellery_order_created = 1
                jewellery_order_count += 1
            frappe.msgprint(
                f"{jewellery_order_count} Jewellery Orders Created.",
                indicator="green",
                alert=1,
            )
        else:
            frappe.throw(_(f"Jewellery Order is already exist for {self.name}"))
