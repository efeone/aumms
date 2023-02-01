# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from aumms.aumms.utils import *

class PurityConversionTool(Document):
	def validate(self):
		frappe.throw(_('No Permision To Save!'))

	@frappe.whitelist()
	def add_gw_and_aw(self):
		"""
			function to add Gold Weight and Alloy Weight
			output: dict of aw and gw
		"""
		gw, aw = 0.0, 0.0
		if self.uom and self.conversion_charts:
			for row in self.conversion_charts:
				if row.stock_uom == self.uom:
					gw += row.gold_weight_to_be_obtained_for_the_purity
					aw += row.alloy_weight
				else:
					# multiply weight with conversion factor
					conversion_factor = get_conversion_factor(row.stock_uom, self.uom)
					if conversion_factor:
						gw_after_converted = row.gold_weight_to_be_obtained_for_the_purity * conversion_factor
						aw_after_converted = row.alloy_weight * conversion_factor
						gw += gw_after_converted
						aw += aw_after_converted
					else:
						# message to user about set conversion factor value
						frappe.throw(
							_('Please set Conversion Factor for {0} to {1}'.format(row.stock_uom, self.uom))
						)
		return {'gw': gw, 'aw': aw}

@frappe.whitelist()
def get_metal_ledger_entries(party_type, party, item_type, purity):
	''' Method to get Metal Ledger Entries '''
	field_list = ['name', 'item_code', 'item_name', 'in_qty', 'stock_uom', 'purity', 'purity_percentage']
	metal_ledger_entries = frappe.db.get_all('Metal Ledger Entry', filters = { 'party_type': party_type, 'party':party, 'item_type':item_type , 'is_cancelled': 0 }, fields = field_list )
	for ml_entry in metal_ledger_entries:
		ml_entry['purity_to_be_obtained'] = frappe.db.get_value('Purity', purity, 'purity_percentage')
		if ml_entry.purity:
			ml_entry['gold_in_hand_purity'] = frappe.db.get_value('Purity', ml_entry.purity, 'purity_percentage')
		if ml_entry.in_qty and ml_entry.purity_percentage:
			ml_entry['gold_weight'] = get_gold_weight_for_purity(float(ml_entry.in_qty), float(ml_entry.purity_percentage), purity)
		else:
			ml_entry['gold_weight'] = 0
		if ml_entry.gold_weight < ml_entry.in_qty:
			ml_entry['alloy_weight'] = ml_entry.in_qty - ml_entry.gold_weight
		else:
			ml_entry['alloy_weight'] = ml_entry.gold_weight - ml_entry.in_qty
	return metal_ledger_entries


@frappe.whitelist()
def get_gold_weight_for_purity(gold_in_hand_weight, gold_in_hand_purity, purity):
	'''method to get calculate gold weight to given purity'''
	gold_weight = 0;
	purity_percentage = 1;
	if gold_in_hand_weight and gold_in_hand_purity and purity:
		purity_percentage = frappe.db.get_value('Purity', purity, 'purity_percentage')
		gold_weight = gold_in_hand_weight * (gold_in_hand_purity/purity_percentage)
	return gold_weight;
