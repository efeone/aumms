# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CustomerJewelleryOrder(Document):
	pass

@frappe.whitelist()
def create_jewellery_order(customer_jewellery_order):
    if frappe.db.exists('Customer Jewellery Order', customer_jewellery_order):
        doc = frappe.get_doc('Customer Jewellery Order', customer_jewellery_order)
        if not frappe.db.exists('Jewellery Order', {'customer_jewellery_order': doc.name}):
            for item in doc.order_item:
                jewellery_order = frappe.new_doc('Jewellery Order')
                jewellery_order.customer_jewellery_order = doc.name
                jewellery_order.customer = doc.customer
                jewellery_order.required_date = doc.required_date
                jewellery_order.customer_expected_total_weight = doc.customer_expected_total_weight
                jewellery_order.customer_expected_amount = doc.customer_expected_amount
                jewellery_order.item_category = item.item_category
                jewellery_order.item_type = item.item_type
                jewellery_order.quantity = item.item_quantity
                jewellery_order.expected_weight_per_quantity = item.expected_weight_per_quantity
                jewellery_order.design_attachment = item.item_design_attachment
                jewellery_order.insert(ignore_permissions=True)
                frappe.msgprint('Jewellery Order Created.', indicator="green", alert=1)
        else:
            frappe.throw(_('Jewellery Order is already exist for {0}'.format(doc.name)))
    else:
        frappe.throw(_('Customer Jewellery Order {0} does not exist'.format(customer_jewellery_order)))
