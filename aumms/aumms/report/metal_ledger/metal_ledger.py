# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import *
from frappe import _
from aumms.aumms.utils import get_party_link_if_exist, get_conversion_factor

def execute(filters=None):
	columns, data = get_columns(filters), get_data(filters)
	return columns, data

def get_columns(filters):
	''' Method to get columns in report '''
	columns = [
		{'label': _('Posting Date'), 'fieldtype': 'Date', 'width': 110},
	    {'label': _('Item Code'), 'fieldtype': 'Link', 'options': 'Item', 'width': 110},
		{'label': _('Party Type'), 'fieldname': 'party_type', 'fieldtype': 'Link', 'options': 'DocType', 'hidden': 1 },
		{'label': _('Party'), 'fieldtype': 'Dynamic Link', 'options': 'party_type', 'width': 130},
		{'label': _('Item Type'), 'fieldtype': 'Link', 'options': 'Item Type', 'width': 100, 'hidden': 1},
		{'label': _('Purity'), 'fieldtype': 'Link', 'options': 'Purity', 'width': 75, 'hidden': 1},
		{'label': _('In Quantity'), 'fieldname': 'in_qty', 'fieldtype': 'Float', 'width': 100},
		{'label': _('Out Quantity'), 'fieldname': 'out_qty', 'fieldtype': 'Float', 'width': 120},
		{'label': _('Balance Quantity'), 'fieldname': 'balance_qty', 'fieldtype': 'Float', 'width': 150},
		{'label': _('Stock UOM'), 'fieldtype': 'Link', 'options': 'UOM', 'width': 100, 'hidden': 1},
		{'label': _('Party Type'), 'fieldtype': 'Data', 'width': 100, 'hidden': 1},
		{'label': _('Voucher Type'), 'fieldtype': 'Link', 'options': 'DocType', 'fieldname': 'voucher_type', 'hidden': 1},
		{'label': _('Voucher No'), 'fieldtype': 'Dynamic Link', 'options': 'voucher_type', 'width': 200},
		{'label': _('Incoming Rate'), 'fieldname': 'in_rate', 'fieldtype': 'Currency', 'width': 120},
		{'label': _('Outgoing Rate'), 'fieldname': 'out_rate', 'fieldtype': 'Currency', 'width': 120},
		{'label': _('Amount'), 'fieldname': 'amount', 'fieldtype': 'Currency', 'width': 110},
		{'label': _('Posting Time'), 'fieldtype': 'Time', 'width': 110},
		]
	if filters.purity and filters.uom:
		columns.insert(9, {'label': _('Balance Quantity'), 'fieldname': 'balance_qty', 'fieldtype': 'Float', 'width': 150})
	return columns

def get_data(filters):
	''' Method to get data '''
	get_filters(filters)
	data = []
	metal_ledger_entry_list = frappe.get_all('Metal Ledger Entry', order_by='creation desc', filters=get_filters(filters))
	for metal_ledger_entry in metal_ledger_entry_list:
		doc = frappe.get_doc('Metal Ledger Entry', metal_ledger_entry.name)
		row = [
			doc.posting_date,
			doc.item_code,
			doc.party_type,
			doc.party,
			doc.item_type,
			doc.purity,
			doc.stock_uom,
			doc.in_qty,
			doc.out_qty,
			doc.balance_qty,
			doc.stock_uom,
			doc.party_type,
			doc.voucher_type,
			doc.voucher_no,
			doc.incoming_rate,
			doc.outgoing_rate,
			doc.amount,
			doc.posting_time
		]
		if filters.purity and filters.uom:
			balance_qty = get_balance_qty(doc.creation, doc.item_type, doc.party_link, filters.purity, filters.uom)
			row.insert(9, balance_qty)
		data.append(row)
	return data

def get_filters(filters):
	''' Method to get filters '''
	conditions = {}
	if filters.company:
		conditions['company'] = filters.company
	if filters.from_date and filters.to_date:
		conditions['posting_date'] = [ 'between' , [ getdate(filters.from_date), getdate(filters.to_date) ] ]
	if filters.item_code:
		conditions['item_code'] = filters.item_code
	if filters.item_type:
		conditions['item_type'] = filters.item_type
	if filters.party_type and not filters.party:
		conditions['party_type'] = filters.party_type
	if filters.party:

		# to show common party accounts
		if filters.common_party:

			# get party link of this party
			party_link = get_party_link_if_exist(filters.party_type, filters.party)
			conditions['party_link'] = party_link

		else:
			# update condition with party
			conditions['party'] = filters.party

	if filters.voucher_type:
		conditions['voucher_type'] = filters.voucher_type
	if filters.voucher_no:
		conditions['voucher_no'] = filters.voucher_no
	if filters.item_type:
		conditions['item_type'] = filters.item_type
	if conditions:
		return conditions
	else:
		return []

def get_balance_qty(creation, item_type, party_link, purity, uom):
	"""
		method to get balance qty of a an item type of a
		common account party with conversion of purity and uom
		args:
			creation: creation datetime of ledger document
			item_type: item type link
			party_link: name of party link
			purity: purity set in the filter
			uom: uom set in the filter
		output: balance qty of an item type of a common account party in filter uom and purity
	"""
	ledgers = frappe.db.get_all('Metal Ledger Entry',
		filters = {
			'creation': ['<=', creation],
			'item_type': item_type,
			'party_link': party_link,
			'is_cancelled': 0
		},
		fields = [
			'in_qty', 'out_qty', 'stock_uom', 'purity_percentage', 'purity'
		]
	)

	balance = 0
	purity_percentage = frappe.db.get_value('Purity', purity, 'purity_percentage')

	for ledger in ledgers:
		qty = ledger.in_qty if ledger.in_qty else -ledger.out_qty
		# update balance qty
		if ledger.stock_uom == uom:
			if ledger.purity == purity:
				balance += qty
			else:
				# convert purity
				purity_converted_qty = (qty * float(ledger.purity_percentage))/float(purity_percentage)
				balance += purity_converted_qty
		else:
			# update qty with conversion factor
			conversion_factor = get_conversion_factor(ledger.stock_uom, uom)
			if not conversion_factor:
				frappe.throw(_('Please set Conversion Factor for {0} to {1}'.format(ledger.stock_uom, uom)))
			qty *= conversion_factor
			if ledger.purity == purity:
				balance += qty
			else:
				# convert purity
				purity_converted_qty = (qty * float(ledger.purity_percentage))/float(purity_percentage)
				balance += purity_converted_qty
	return balance
