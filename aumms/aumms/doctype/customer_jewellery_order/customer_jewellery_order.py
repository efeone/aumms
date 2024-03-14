# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _


class CustomerJewelleryOrder(Document):

    def validate(self):
        if self.total_expected_weight_per_quantity != self.customer_expected_total_weight:
            frappe.throw(_('The Sum of Expected Weights Per Quantity must be Equal to Customer Expected Weight'))
