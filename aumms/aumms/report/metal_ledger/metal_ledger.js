// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports['Metal Ledger'] = {
	'filters': [
		{
			'fieldname': 'company',
			'label': __('Company'),
			'fieldtype': 'Link',
			'options': 'Company',
			'default': frappe.defaults.get_user_default('Company'),
			'reqd': 1
		},
		{
			'fieldname': 'from_date',
			'label': __('From Date'),
			'fieldtype': 'Date',
			'default': frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			'reqd': 1
		},
		{
			'fieldname': 'to_date',
			'label': __('To Date'),
			'fieldtype': 'Date',
			'default': frappe.datetime.get_today(),
			'reqd': 1
		},
		{
			'fieldname': 'item_code',
			'label': __('Item'),
			'fieldtype': 'Link',
			'options': 'Item',
			'get_query': function() {
				return {
					query: 'erpnext.controllers.queries.item_query'
				}
			}
		},
		{
			'fieldname': 'item_type',
			'label': __('Item Type'),
			'fieldtype': 'Link',
			'options': 'Item Type'
		},
		{
			'fieldname': 'batch_no',
			'label': __('Batch No'),
			'fieldtype': 'Link',
			'options': 'Batch'
		},
		{
			'fieldname': 'voucher_type',
			'label': __('Voucher Type'),
			'fieldtype': 'Link',
			'options': 'DocType',
			'get_query': function() {
				return {
					'filters': {
						'name': ['in',['Sales Invoice', 'Purchase Receipt']]
					}
				}
			}
		},
		{
			'fieldname': 'voucher_no',
			'label': __('Voucher No'),
			'fieldtype': 'Data',
		},
		{
			'fieldname': 'uom',
			'label': __('UOM'),
			'fieldtype': 'Link',
			'options': 'UOM'
		},
		{
			'fieldname': 'party_type',
			'label': __('Party Type'),
			'fieldtype': 'Link',
			'options': 'DocType',
			'get_query': function() {
				return {
					'filters': {
						'name': ['in',['Supplier', 'Customer']]
					}
				}
			}
		},
		{
			'fieldname': 'party',
			'label': __('Party'),
			'fieldtype': 'Dynamic Link',
			'options': 'party_type'
		},
		{
			'fieldname': 'common_party',
			'label': __('Common Party Account'),
			'fieldtype': 'Check',
			'default': 1,
			'depends_on': 'party'
		}
	],
	'formatter': function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if ((column.fieldname == 'out_rate' && data && data.out_rate > 0)||(column.fieldname == 'out_qty' && data && data.out_qty > 0)) {
			value = "<span style='color:red'>" + value + "</span>";
		}
		else if ((column.fieldname == 'in_rate' && data && data.in_rate > 0)||(column.fieldname == 'in_qty' && data && data.in_qty > 0)) {
			value = "<span style='color:green'>" + value + "</span>";
		}
		if ((column.fieldname == 'balance_qty' && data && data.balance_qty > 0)||(column.fieldname == 'amount' && data && data.amount > 0)) {
			value = "<span style='color:green'>" + value + "</span>";
		}
		else if ((column.fieldname == 'balance_qty' && data && data.balance_qty < 0)||(column.fieldname == 'amount' && data && data.amount < 0)) {
			value = "<span style='color:red'>" + value + "</span>";
		}
		return value;
	}
};
