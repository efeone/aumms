# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CustomerJewelleryOrder(Document):
    def validate(self):
        if (
            self.total_expected_weight_per_quantity
            != self.customer_expected_total_weight
        ):
            frappe.throw(
                _(
                    "The Sum of Expected Weights Per Quantity must be Equal to Customer Expected Weight"
                )
            )

    def on_submit(self):
        self.create_jewellery_order()

    def create_jewellery_order(self):
        jewellery_order_exist = frappe.db.exists(
            "Jewellery Order", {"customer_jewellery_order": self.name}
        )
        if not jewellery_order_exist:
            for item in self.order_item:
                new_jewellery_order = frappe.new_doc("Jewellery Order")
                new_jewellery_order.customer_jewellery_order = self.name
                new_jewellery_order.customer = self.customer
                new_jewellery_order.required_date = self.required_date
                new_jewellery_order.uom = self.uom
                new_jewellery_order.purity = self.purity
                new_jewellery_order.customer_expected_total_weight = (
                    item.expected_weight_per_quantity
                )
                new_jewellery_order.customer_expected_amount = (
                    self.customer_expected_amount
                )
                new_jewellery_order.uom = self.uom
                new_jewellery_order.purity = self.purity
                new_jewellery_order.category = item.item_category
                new_jewellery_order.type = item.item_type
                new_jewellery_order.quantity = item.item_quantity
                new_jewellery_order.expected_weight_per_quantity = (
                    item.expected_weight_per_quantity
                )
                new_jewellery_order.design_attachment = item.item_design_attachment
                new_jewellery_order.insert(ignore_permissions=True)
                frappe.msgprint(
                    f"Jewellery Order {new_jewellery_order.name} Created.",
                    indicator="green",
                    alert=1,
                )
        else:
            frappe.throw(_(f"Jewellery Order is already exist for {self.name}"))

    @frappe.whitelist()
    def calculate_customer_expected_amount(self):
        exists = frappe.db.exists("Board Rate", {"purity": self.purity, "uom": "Gram"})
        if exists:
            latest_board_rate = frappe.get_last_doc(
                "Board Rate", {"purity": self.purity, "uom": "Gram"}
            )
            board_rate_value = latest_board_rate.board_rate
            self.customer_expected_amount = (
                self.customer_expected_total_weight * board_rate_value
            )
        else:
            frappe.throw(
                f"No Board Rate found for Purity {self.purity} and UOM {self.uom}"
            )
