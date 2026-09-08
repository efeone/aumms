# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

from datetime import timedelta

import frappe
from frappe import _
from frappe.utils.data import date_diff, flt, fmt_money, formatdate, getdate

from aumms.aumms.utils import get_conversion_factor, get_party_link_if_exist

ENTRY_FIELDS = [
	"posting_date",
	"posting_time",
	"item_code",
	"party_type",
	"party",
	"item_type",
	"purity",
	"purity_percentage",
	"stock_uom",
	"in_qty",
	"out_qty",
	"voucher_type",
	"voucher_no",
	"incoming_rate",
	"outgoing_rate",
	"amount",
	"is_cancelled",
	"creation",
]

# what a balance is read from, which is less than a row of the report needs
MOVEMENT_FIELDS = [
	"posting_date",
	"posting_time",
	"creation",
	"in_qty",
	"out_qty",
	"stock_uom",
	"purity",
	"purity_percentage",
]

# the order metal moves in, which the running balance has to follow
ENTRY_ORDER = "posting_date asc, posting_time asc, creation asc"

# a weight is quoted to the milligram, the way the trade quotes it
QTY_PRECISION = 3

# the day count above which the trend chart is read by month rather than by day
DAILY_TREND_DAYS = 92

IN_COLOR = "#48bb74"
OUT_COLOR = "#e24c4c"
BALANCE_COLOR = "#5e64ff"


def execute(filters=None):
	# the rows, the tiles and the chart are all read from the one pass over the movements,
	# so they cannot drift apart from each other as the filters change.
	movements = get_movements(filters) if show_balance(filters) else None
	columns = get_columns(filters)
	data = get_data(filters, movements)
	report_summary = get_report_summary(filters, movements)
	return columns, data, None, get_chart(filters, movements), report_summary


def get_columns(filters):
	"""Method to get columns in report"""
	columns = [
		{"label": _("Posting Date"), "fieldtype": "Date", "width": 110},
		{"label": _("Item Code"), "fieldtype": "Link", "options": "Item", "width": 110},
		{
			"label": _("Party Type"),
			"fieldname": "party_type",
			"fieldtype": "Link",
			"options": "DocType",
		},
		{
			"label": _("Party"),
			"fieldtype": "Dynamic Link",
			"options": "party_type",
			"width": 130,
		},
		{
			"label": _("Item Type"),
			"fieldtype": "Link",
			"options": "Item Type",
			"width": 100,
		},
		{
			"label": _("Purity of Transaction"),
			"fieldtype": "Link",
			"options": "Purity",
			"width": 175,
		},
		{"label": _("Weight UOM"), "fieldtype": "Link", "options": "UOM", "width": 100},
		{
			"label": _("In Quantity"),
			"fieldname": "in_qty",
			"fieldtype": "Float",
			"width": 100,
		},
		{
			"label": _("Out Quantity"),
			"fieldname": "out_qty",
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"label": _("Voucher Type"),
			"fieldtype": "Link",
			"options": "DocType",
			"fieldname": "voucher_type",
			"hidden": 1,
		},
		{
			"label": _("Voucher No"),
			"fieldtype": "Dynamic Link",
			"options": "voucher_type",
			"width": 200,
		},
		{
			"label": _("Incoming Rate"),
			"fieldname": "in_rate",
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"label": _("Outgoing Rate"),
			"fieldname": "out_rate",
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"label": _("Amount"),
			"fieldname": "amount",
			"fieldtype": "Currency",
			"width": 110,
		},
		{"label": _("Posting Time"), "fieldtype": "Time", "width": 110},
	]
	if show_balance(filters):
		columns.insert(
			9,
			{
				"label": _("Balance Quantity"),
				"fieldname": "balance_qty",
				"fieldtype": "Float",
				"width": 150,
			},
		)
	return columns


def show_balance(filters):
	"""a balance can only be stated in a purity and a weight uom, so both have to be asked for"""
	return bool(filters.purity and filters.uom)


def get_data(filters, movements=None):
	"""
	Method to get data

	args:
					filters: filters selected in the report
					movements: movements of the metal, when a balance is on show
	output: rows of the report, newest first
	"""
	# the rows are read oldest first to be walked alongside the running balance, and are
	# turned around at the end to leave the report newest first.
	entries = frappe.get_all(
		"Metal Ledger Entry",
		filters=get_filters(filters),
		fields=ENTRY_FIELDS,
		order_by=ENTRY_ORDER,
	)

	balance = movements.opening if movements else 0
	purity_percentage = get_purity_percentage(filters.purity) if movements else 0
	index = 0
	data = []
	for entry in entries:
		in_qty, out_qty = entry.in_qty, entry.out_qty
		if movements:
			# a row is weighed the way the balance beside it and the tiles above it are, or
			# metal held in another uom would read as a quantity the balance never moved by
			in_qty, out_qty = get_row_qty(entry, filters, purity_percentage)
		elif filters.purity:
			in_qty, out_qty = get_purity_converted_qty(
				entry.purity, entry.in_qty, entry.out_qty, filters.purity
			)
		row = [
			entry.posting_date,
			entry.item_code,
			entry.party_type,
			entry.party,
			entry.item_type,
			entry.purity or "22k", # CHANGE THIS!
			filters.uom if movements else entry.stock_uom,
			in_qty,
			out_qty,
			entry.voucher_type,
			entry.voucher_no,
			entry.incoming_rate,
			entry.outgoing_rate,
			entry.amount,
			entry.posting_time,
		]
		if movements:
			# the balance the metal stood at once this row had moved. A row the voucher
			# filters left out of the report still moved it, so the balance is walked
			# alongside the rows instead of being added up from them.
			entry_key = get_sort_key(entry)
			while (
				index < len(movements.balances) and movements.balances[index][0] <= entry_key
			):
				balance = movements.balances[index][1]
				index += 1
			row.insert(9, balance)
		data.append(row)

	data.reverse()
	return data


def get_filters(filters):
	"""Method to get filters, which pick the rows the report lists"""
	conditions = get_balance_filters(filters)
	# a cancelled entry is left out unless it is asked for, the way the Stock Ledger hides its
	# own. The button on a cancelled voucher asks for them, or it would open an empty report.
	if not filters.get("show_cancelled_entries"):
		conditions["is_cancelled"] = 0
	if filters.from_date and filters.to_date:
		conditions["posting_date"] = [
			"between",
			[getdate(filters.from_date), getdate(filters.to_date)],
		]
	if filters.voucher_type:
		conditions["voucher_type"] = filters.voucher_type
	if filters.voucher_no:
		conditions["voucher_no"] = filters.voucher_no
	return conditions


def get_balance_filters(filters):
	"""
	method to get the filters that pick the metal a balance is held for

	A balance is a holding rather than a list of rows, so it follows the company, item, item
	type, batch and party asked for, but not the voucher filters, which only say which of
	that metal's movements are on show.

	args:
					filters: filters selected in the report
	output: conditions dict matching every entry of the metal in question
	"""
	conditions = {}
	if filters.company:
		conditions["company"] = filters.company
	if filters.item_code:
		conditions["item_code"] = filters.item_code
	if filters.item_type:
		conditions["item_type"] = filters.item_type
	if filters.batch_no:
		conditions["batch_no"] = filters.batch_no
	if filters.party_type and not filters.party:
		conditions["party_type"] = filters.party_type
	if filters.party:

		# to show common party accounts, which only a Customer or a Supplier can hold. A
		# smith takes metal without an account of their own, so it is matched by name.
		if filters.common_party and filters.party_type in ("Customer", "Supplier"):

			# get party link of this party
			party_link = get_party_link_if_exist(filters.party_type, filters.party)
			conditions["party_link"] = party_link

		else:
			# update condition with party
			conditions["party"] = filters.party

	return conditions


def get_movements(filters):
	"""
	method to read every movement of the metal over the range, in one pass

	The report answers for one holding of metal, so the balance, the tiles and the charts are
	all read from these movements, under the same filters and in the purity and uom asked for.

	args:
					filters: filters selected in the report
	output: dict of the opening and closing balance, the totals in and out, the balance each
					movement left behind, and the movement grouped by period and by purity
	"""
	conditions = get_balance_filters(filters)
	conditions["is_cancelled"] = 0
	conditions["posting_date"] = [
		"between",
		[getdate(filters.from_date), getdate(filters.to_date)],
	]

	entries = frappe.get_all(
		"Metal Ledger Entry",
		filters=conditions,
		fields=MOVEMENT_FIELDS,
		order_by=ENTRY_ORDER,
	)

	opening_balance = get_opening_balance(filters)
	purity_percentage = get_purity_percentage(filters.purity)
	by_month = (
		date_diff(getdate(filters.to_date), getdate(filters.from_date)) > DAILY_TREND_DAYS
	)
	movements = frappe._dict(
		opening=opening_balance,
		closing=opening_balance,
		total_in=0,
		total_out=0,
		balances=[],
		by_period={},
		by_purity={},
	)

	for entry in entries:
		qty = get_converted_qty(entry, filters.purity, filters.uom, purity_percentage)
		movements.closing += qty
		movements.balances.append((get_sort_key(entry), movements.closing))

		# the entries come in oldest first, so a period keeps its place by being met first
		period = movements.by_period.setdefault(
			get_period(entry.posting_date, by_month),
			frappe._dict(in_qty=0, out_qty=0, balance=0),
		)
		purity = movements.by_purity.setdefault(
			entry.purity, frappe._dict(in_qty=0, out_qty=0)
		)

		# metal that raises the balance came in, whichever field it was written in
		if qty >= 0:
			movements.total_in += qty
			period.in_qty += qty
			purity.in_qty += qty
		else:
			movements.total_out += -qty
			period.out_qty += -qty
			purity.out_qty += -qty
		period.balance = movements.closing

	return movements


def get_period(posting_date, by_month):
	"""the label a movement is grouped under on the trend chart"""
	if by_month:
		return getdate(posting_date).strftime("%b %Y")
	return formatdate(posting_date)


def get_opening_balance(filters):
	"""
	method to get the balance carried into from_date

	args:
					filters: filters selected in the report
	output: balance qty before from_date, in the purity and uom asked for
	"""
	conditions = get_balance_filters(filters)
	conditions["is_cancelled"] = 0
	conditions["posting_date"] = ["<", getdate(filters.from_date)]

	entries = frappe.get_all(
		"Metal Ledger Entry",
		filters=conditions,
		fields=["in_qty", "out_qty", "stock_uom", "purity", "purity_percentage"],
	)

	purity_percentage = get_purity_percentage(filters.purity)
	balance = 0
	for entry in entries:
		balance += get_converted_qty(entry, filters.purity, filters.uom, purity_percentage)
	return balance


def get_sort_key(entry):
	"""the place of an entry in the order metal moves, creation settling entries of one moment"""
	return (entry.posting_date, entry.posting_time or timedelta(0), entry.creation)


def get_converted_qty(entry, purity, uom, purity_percentage):
	"""
	method to get the qty one ledger entry moves, in the purity and uom of the filters

	args:
					entry: metal ledger entry holding in_qty, out_qty, stock_uom and purity
					purity: purity set in the filter
					uom: uom set in the filter
					purity_percentage: purity percentage of the purity set in the filter
	output: signed qty of the entry, positive for metal in and negative for metal out
	"""
	qty = entry.in_qty if entry.in_qty else -entry.out_qty
	if entry.stock_uom != uom:
		conversion_factor = get_conversion_factor(entry.stock_uom, uom)
		if not conversion_factor:
			frappe.throw(
				_("Please set Conversion Factor for {0} to {1}").format(entry.stock_uom, uom)
			)
		qty *= conversion_factor
	if entry.purity != purity:
		entry_percentage = (
			float(entry.purity_percentage)
			if entry.purity_percentage
			else get_purity_percentage(entry.purity)
		)
		qty = (qty * entry_percentage) / purity_percentage
	return qty


def get_row_qty(entry, filters, purity_percentage):
	"""method to get the qty a row moved, in and out, in the purity and uom of the filters"""
	qty = get_converted_qty(entry, filters.purity, filters.uom, purity_percentage)
	if qty >= 0:
		return qty, 0
	return 0, -qty


def get_purity_percentage(purity):
	"""method to get the purity percentage of a purity, which every conversion divides by"""
	purity_percentage = frappe.db.get_value("Purity", purity, "purity_percentage")
	if not purity_percentage:
		frappe.throw(_("Please set Purity Percentage in Purity {0}").format(purity))
	return float(purity_percentage)


def get_purity_converted_qty(ledger_purity, in_qty, out_qty, filter_purity):
	if ledger_purity == filter_purity:
		return in_qty, out_qty
	ledger_purity_percentage = frappe.db.get_value(
		"Purity", ledger_purity, "purity_percentage"
	)
	filter_purity_percentage = frappe.db.get_value(
		"Purity", filter_purity, "purity_percentage"
	)
	purity_converted_in_qty = 0
	if not ledger_purity_percentage:
		ledger_purity_percentage = 91.67 # CHANGE THIS!
	if in_qty:
		purity_converted_in_qty = (
			in_qty * ledger_purity_percentage
		) / filter_purity_percentage
	purity_converted_out_qty = (
		out_qty * ledger_purity_percentage
	) / filter_purity_percentage
	return purity_converted_in_qty, purity_converted_out_qty


def get_report_summary(filters, movements):
	"""Generates Report Summary object

	Args:
		filters (frappe dict): contains filters selected in the report
		movements (frappe dict): movements of the metal, or None when no balance is on show

	Returns:
		list of dict: each dict containing the details of summary to be displayed
	"""
	if not movements:
		# never an empty list, as the desk only redraws the tiles when it is handed some and
		# would leave the ones read under the last filters standing.
		return [
			{
				"value": _("Set Purity and Weight UOM to see balances"),
				"label": _("Balance"),
				"datatype": "Data",
			}
		]

	net = movements.total_in - movements.total_out
	return [
		{
			"value": format_qty(movements.opening, filters.uom),
			"indicator": "Blue",
			"label": _("Opening Balance"),
			"datatype": "Data",
		},
		{
			"value": format_qty(movements.total_in, filters.uom),
			"indicator": "Green",
			"label": _("Total In"),
			"datatype": "Data",
		},
		{
			"value": format_qty(movements.total_out, filters.uom),
			"indicator": "Red",
			"label": _("Total Out"),
			"datatype": "Data",
		},
		{
			"value": format_qty(net, filters.uom, signed=True),
			"indicator": "Green" if net >= 0 else "Red",
			"label": _("Net Movement"),
			"datatype": "Data",
		},
		{
			"value": format_qty(movements.closing, filters.uom),
			"indicator": "Green" if movements.closing >= 0 else "Red",
			"label": _("Closing Balance"),
			"datatype": "Data",
		},
	]


def format_qty(qty, uom, signed=False):
	"""a weight reads with the uom it was weighed in, which a tile has no column for"""
	value = fmt_money(flt(qty, QTY_PRECISION), precision=QTY_PRECISION)
	if signed and qty > 0:
		value = "+" + value
	return "{0} {1}".format(value, uom)


def get_chart(filters, movements):
	"""
	method to get the chart of metal moving in and out over the range

	args:
					filters: filters selected in the report
					movements: movements of the metal, or None when no balance is on show
	output: chart of the metal in and out of each period, over the balance it left behind
	"""
	if not movements or not movements.by_period:
		return None

	periods = list(movements.by_period.values())
	return {
		"data": {
			"labels": list(movements.by_period.keys()),
			"datasets": [
				{
					"name": _("In"),
					"chartType": "bar",
					"values": [flt(period.in_qty, QTY_PRECISION) for period in periods],
				},
				{
					"name": _("Out"),
					"chartType": "bar",
					"values": [flt(period.out_qty, QTY_PRECISION) for period in periods],
				},
				{
					"name": _("Balance"),
					"chartType": "line",
					"values": [flt(period.balance, QTY_PRECISION) for period in periods],
				},
			],
		},
		"title": _("Metal Movement ({0})").format(filters.uom),
		"type": "axis-mixed",
		"colors": [IN_COLOR, OUT_COLOR, BALANCE_COLOR],
		"fieldtype": "Float",
		"barOptions": {"spaceRatio": 0.4},
		"lineOptions": {"regionFill": 0},
	}


@frappe.whitelist()
def get_purity_chart(filters=None):
	"""
	method to get the chart of metal moving at each purity it was traded in

	The desk hands a report one chart area, so this one is asked for on its own and drawn
	beside it. It reads the same movements as the report, converted to the purity in the
	filter, so its bars add up to the totals on the tiles.

	args:
					filters: filters selected in the report
	output: chart of the metal in and out at each purity, or None when there is none to show
	"""
	frappe.has_permission("Metal Ledger Entry", throw=True)

	filters = frappe._dict(frappe.parse_json(filters) or {})
	if not show_balance(filters) or not (filters.from_date and filters.to_date):
		return None

	movements = get_movements(filters)
	if not movements.by_purity:
		return None

	# the purity that moved the most metal reads first, the way the trade looks at it
	purities = sorted(
		movements.by_purity.items(),
		key=lambda purity: purity[1].in_qty + purity[1].out_qty,
		reverse=True,
	)
	return {
		"data": {
			"labels": [purity for purity, movement in purities],
			"datasets": [
				{
					"name": _("In"),
					"values": [
						flt(movement.in_qty, QTY_PRECISION) for purity, movement in purities
					],
				},
				{
					"name": _("Out"),
					"values": [
						flt(movement.out_qty, QTY_PRECISION) for purity, movement in purities
					],
				},
			],
		},
		"title": _("Movement by Purity (in {0} {1})").format(filters.purity, filters.uom),
		"type": "bar",
		"colors": [IN_COLOR, OUT_COLOR],
		"fieldtype": "Float",
		"barOptions": {"spaceRatio": 0.4},
	}
