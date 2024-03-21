# Copyright (c) 2024, efeone and contributors
# For license information, please see license.txt
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc


class ManufacturingRequest(Document):
	pass

@frappe.whitelist()
def create_required_raw_material(source_name, target_doc=None):
    def set_missing_values(source, target):
        target.jewellery_order = source.jewellery_order
        target.manufacturing_request = source.name
        target.item_required_date = source.required_date
        target.total_quantity = source.quantity
        target.total_weight = source.total_weight

    doc = get_mapped_doc(
        'Manufacturing Request',
        source_name,
        {
            'Manufacturing Request': {
                'doctype': 'Raw Material Required',
            },
        },
        target_doc,
        set_missing_values
    )

    return doc
