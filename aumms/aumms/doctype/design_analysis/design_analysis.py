# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class DesignAnalysis(Document):
    pass

@frappe.whitelist()
def fetch_design_details(parent):
	design_details = frappe.get_all(
		'Design Details',
		filters={'parenttype': 'Design Request', 'parent': parent},
		fields=['material', 'item_type', 'purity', 'unit_of_measure', 'quantity', 'is_customer_provided']
	)

	return design_details


    