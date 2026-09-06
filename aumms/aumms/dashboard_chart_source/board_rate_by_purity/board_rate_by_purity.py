# Copyright (c) 2026, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import add_days, flt, getdate, nowdate
from frappe.utils.dashboard import cache_source
from frappe.utils.dateutils import (
	get_dates_from_timegrain,
	get_from_date_from_timespan,
	get_period,
)

# a purity whose last rate is older than this is treated as no longer quoted
SEED_LOOKBACK_DAYS = 365


@frappe.whitelist()
@cache_source
def get(
	chart_name=None,
	chart=None,
	no_cache=None,
	filters=None,
	from_date=None,
	to_date=None,
	timespan=None,
	time_interval=None,
	heatmap_year=None,
):
	"""
	Board rate over time, one line per purity.
		output: labels and one dataset per purity, in the shape frappe charts expects
	"""
	if chart_name:
		chart = frappe.get_doc("Dashboard Chart", chart_name)
	else:
		chart = frappe._dict(frappe.parse_json(chart))

	timespan = timespan or chart.timespan
	timegrain = time_interval or chart.time_interval

	if timespan == "Select Date Range":
		from_date = from_date or chart.from_date
		to_date = to_date or chart.to_date
	else:
		# a stale date range saved against the widget must not outrank the timespan
		from_date = to_date = None

	to_date = getdate(to_date or nowdate())
	from_date = getdate(from_date) if from_date else getdate(get_from_date_from_timespan(to_date, timespan))

	item_type = get_item_type_filter(filters, chart)
	dates = get_dates_from_timegrain(from_date, to_date, timegrain)
	rates = get_board_rates(from_date, to_date, item_type)
	datasets = build_datasets(dates, rates)

	# an empty result makes the widget show its no data state instead of an empty chart
	if not datasets:
		return {}

	return {
		"labels": [get_period(date, timegrain) for date in dates],
		"datasets": datasets,
	}


def get_item_type_filter(filters, chart):
	"""
	function to read the item type filter set on the chart
		args:
			filters: filters passed by the chart widget
			chart: Dashboard Chart document
		output: name of the item type, or None when the chart is not filtered
	"""
	filters = frappe.parse_json(filters) or frappe.parse_json(chart.filters_json)
	if not isinstance(filters, dict):
		return None

	return filters.get("item_type")


def get_board_rates(from_date, to_date, item_type=None):
	"""
	function to fetch submitted board rates that can affect the charted range
		args:
			from_date: first date on the chart
			to_date: last date on the chart
			item_type: item type to restrict the rates to, optional
		output: list of rates ordered oldest first
	"""
	filters = {
		"docstatus": 1,
		"purity": ["is", "set"],
		"date": ["between", [add_days(from_date, -SEED_LOOKBACK_DAYS), to_date]],
	}
	if item_type:
		filters["item_type"] = item_type

	return frappe.db.get_list(
		"Board Rate",
		fields=["item_type", "purity", "date", "board_rate"],
		filters=filters,
		order_by="date asc, time asc",
	)


def build_datasets(dates, rates):
	"""
	function to turn board rate entries into one series per purity
		args:
			dates: period ending dates on the chart
			rates: board rates ordered oldest first
		output: list of datasets, each holding a rate for every date on the chart
	"""
	keys = sort_series_keys({(rate.item_type, rate.purity) for rate in rates})
	series = {key: [] for key in keys}
	latest = {}
	index = 0

	for date in dates:
		while index < len(rates) and getdate(rates[index].date) <= date:
			rate = rates[index]
			latest[(rate.item_type, rate.purity)] = flt(rate.board_rate)
			index += 1
		for key in keys:
			series[key].append(latest.get(key))

	single_item_type = len({key[0] for key in keys}) == 1
	return [
		{"name": get_series_label(key, single_item_type), "values": backfill_leading_gap(series[key])}
		for key in keys
	]


def sort_series_keys(keys):
	"""
	function to order the series so that colours stay tied to the same purity
		args:
			keys: item type and purity pairs found in the rates
		output: pairs ordered by item type, then by purity percentage, highest first
	"""
	percentages = dict(
		frappe.get_all("Purity", fields=["name", "purity_percentage"], as_list=True)
	)

	return sorted(keys, key=lambda key: (key[0], -flt(percentages.get(key[1])), key[1]))


def get_series_label(key, single_item_type):
	"""
	function to name a series
		args:
			key: item type and purity pair
			single_item_type: whether the chart holds a single item type
		output: the purity on its own, qualified by item type when the chart mixes item types
	"""
	item_type, purity = key
	return purity if single_item_type else f"{item_type} - {purity}"


def backfill_leading_gap(values):
	"""
	function to fill the periods before a purity was first quoted
		args:
			values: rates for one purity, with None for periods that have no rate yet
		output: the same list, flat lined backwards from the first known rate
	"""
	first_rate = next((value for value in values if value is not None), 0)
	for index, value in enumerate(values):
		if value is not None:
			break
		values[index] = first_rate

	return values
