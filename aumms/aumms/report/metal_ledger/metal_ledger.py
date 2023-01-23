# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import *
from frappe import _

def execute(filters=None):
	columns, data = get_columns(), get_data(filters)
	return columns, data

def get_columns():
	''' Method to get columns in report '''
	columns = [
	    {'label': _('Item Code'), 'fieldtype': 'Link', 'options': 'Item', 'width': 100},
		{'label': _('Posting Date'), 'fieldtype': 'Date', 'width': 110},
		{'label': _('Posting Time'), 'fieldtype': 'Time', 'width': 110},
		{'label': _('Voucher Type'), 'fieldtype': 'Link', 'options': 'DocType', 'fieldname': 'voucher_type', 'hidden': 1},
		{'label': _('Voucher No'), 'fieldtype': 'Dynamic Link', 'options': 'voucher_type', 'width': 200},
		{'label': _('Party Type'), 'fieldtype': 'Link', 'options': 'DocType', 'hidden': 1 },
		{'label': _('Party'), 'fieldtype': 'Link', 'options': 'DocType', 'width': 130},
		{'label': _('Item Type'), 'fieldtype': 'Link', 'options': 'Item Type', 'width': 100},
		{'label': _('Purity'), 'fieldtype': 'Link', 'options': 'Purity', 'width': 75},
		{'label': _('Quantity'), 'fieldtype': 'Data', 'width': 80},
		{'label': _('Stock UOM'), 'fieldtype': 'Link', 'options': 'UOM', 'width': 100},
		{'label': _('Board Rate'), 'fieldtype': 'Data', 'width': 100},
		{'label': _('Incoming Rate'), 'fieldtype': 'Data', 'width': 120},
		{'label': _('Outgoing Rate'), 'fieldtype': 'Data', 'width': 120},
		{'label': _('Amount'), 'fieldtype': 'Data', 'width': 110},
		{'label': _('Cancelled'), 'fieldtype': 'Check', 'width': 100}
		]
	return columns

def get_data(filters):
	''' Method to get data '''
	get_filters(filters)
	data = []
	metal_ledger_entry_list = frappe.get_all('Metal Ledger Entry', order_by='creation desc', filters=get_filters(filters))
	for metal_ledger_entry in metal_ledger_entry_list:
		doc = frappe.get_doc('Metal Ledger Entry', metal_ledger_entry.name)
		row = [
			doc.item_code,
			doc.posting_date,
			doc.posting_time,
			doc.voucher_type,
			doc.voucher_no,
			doc.party_type,
			doc.party,
			doc.item_type,
			doc.purity,
			doc.qty,
			doc.stock_uom,
			doc.board_rate,
			doc.incoming_rate,
			doc.outgoing_rate,
			doc.amount,
			doc.is_cancelled
		]
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
	if filters.is_cancelled:
		conditions['is_cancelled'] = filters.is_cancelled
	if filters.purity:
		conditions['purity'] = filters.purity
	if filters.uom:
		conditions['stock_uom'] = filters.uom
	if filters.item_type:
		conditions['item_type'] = filters.item_type
	if filters.party_type:
		conditions['party_type'] = filters.party_type
	if filters.party:
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
