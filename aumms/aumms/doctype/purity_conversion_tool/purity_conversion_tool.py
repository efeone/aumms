# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from aumms.aumms.utils import *
from aumms.aumms.utils import get_party_link_if_exist


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
					aw += row.alloy_weight
					if row.voucher_type == 'Purchase Receipt':
						gw += row.gold_weight_to_be_obtained_for_the_purity
					else:
						gw -= row.gold_weight_to_be_obtained_for_the_purity
				else:
					# multiply weight with conversion factor
					conversion_factor = get_conversion_factor(row.stock_uom, self.uom)
					if conversion_factor:
						gw_after_converted = row.gold_weight_to_be_obtained_for_the_purity * conversion_factor
						aw_after_converted = row.alloy_weight * conversion_factor
						aw += aw_after_converted
						if row.voucher_type == 'Purchase Receipt':
							gw += gw_after_converted
						else:
							gw -= gw_after_converted
					else:
						# message to user about set conversion factor value
						frappe.throw(
							_('Please set Conversion Factor for {0} to {1}'.format(row.stock_uom, self.uom))
						)
		return {'gw': gw, 'aw': aw}

	@frappe.whitelist()
	def get_gold_to_be_obtained(self):
		"""
			method to get gold weight by multiplying gold in hand weight
			with the division of gold purity and needed purity
			output: gold weight and alloy weight
		"""

		hand_gold = self.gold_in_hand
		hand_purity = self.purity_percentage_in_hand
		need_purity = self.purity_percentage_to_be_obtained
		hand_uom = self.uom_of_gold_in_hand
		need_uom = self.uom_of_gold_to_be_obtained

		if hand_gold and hand_gold and need_purity and hand_uom and need_uom:
			gold_weight = hand_gold * (hand_purity/need_purity)
			alloy_weight = hand_gold - gold_weight

			# converting gold weight and alloy weight by conversion factor if uom differs
			if hand_uom != need_uom:
				conversion_factor = get_conversion_factor(hand_uom, need_uom)
				if conversion_factor:
					gold_weight *= conversion_factor
					alloy_weight *= conversion_factor
				else:
					# message to user about set conversion factor value
					frappe.throw(
						_('Please set Conversion Factor for {0} to {1}'.format(hand_uom, need_uom))
					)

			return {'gold_weight': gold_weight, 'alloy_weight': alloy_weight}

@frappe.whitelist()
def get_metal_ledger_entries(party_type, party, item_type, purity):
	''' Method to get Metal Ledger Entries '''
	field_list = ['name', 'voucher_type', 'item_code', 'item_name', 'voucher_type', 'in_qty', 'out_qty', 'stock_uom', 'purity', 'purity_percentage']
	party_link = get_party_link_if_exist(party_type, party)
	if party_link:
		filters = { 'party_link': party_link,  'item_type':item_type , 'is_cancelled': 0 }
	else:
		filters = { 'party_type': party_type, 'party':party, 'item_type':item_type , 'is_cancelled': 0 }
	metal_ledger_entries = frappe.db.get_all('Metal Ledger Entry', filters = filters, fields = field_list )
	for ml_entry in metal_ledger_entries:
		ml_entry['purity_to_be_obtained'] = frappe.db.get_value('Purity', purity, 'purity_percentage')
		if ml_entry.purity:
			ml_entry['gold_in_hand_purity'] = frappe.db.get_value('Purity', ml_entry.purity, 'purity_percentage')
		qty = ml_entry.in_qty if ml_entry.voucher_type == 'Purchase Receipt' else ml_entry.out_qty
		ml_entry['qty'] = qty
		if qty and ml_entry.purity_percentage:
			ml_entry['gold_weight'] = get_gold_weight_for_purity(float(qty), float(ml_entry.purity_percentage), purity)
		else:
			ml_entry['gold_weight'] = 0
		ml_entry['alloy_weight'] = qty - ml_entry.gold_weight
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

@frappe.whitelist()
def get_purity_percentage(purity):
	" function to get purity percentage of a purity"
	return frappe.db.get_value('Purity', purity, 'purity_percentage')