// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports['Metal Ledger'] = {
	onload (report) {
		hook_purity_chart(report)
		// A route that opens the report already says which series it wants to see, so the
		// settings only fill in the ones it left alone.
		if (!frappe.query_report.get_filter_value('uom')) {
			frappe.db.get_single_value('AuMMS Settings', 'metal_ledger_uom')
			.then(uom => {
				frappe.query_report.set_filter_value('uom', uom)
			})
		}
		if (!frappe.query_report.get_filter_value('purity')) {
			frappe.db.get_single_value('AuMMS Settings', 'metal_ledger_purity')
			.then(purity => {
				frappe.query_report.set_filter_value('purity', purity)
			})
		}
		frappe.query_report.refresh();
	},
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
			'options': 'Item Type',
			'get_query': function() {
				return {
					'filters': {
						'is_purity_item': 1
					}
				}
			}
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
			'options': 'UOM',
			'get_query': function() {
				return {
					'filters': {
						is_purity_uom: 1,
						enabled: 1
					}
				}
			}
		},
		{
			'fieldname': 'purity',
			'label': __('Purity'),
			'fieldtype': 'Link',
			'options': 'Purity'
		},
		{
			'fieldname': 'party_type',
			'label': __('Party Type'),
			'fieldtype': 'Link',
			'options': 'DocType',
			'get_query': function() {
				return {
					'filters': {
						'name': ['in',['Supplier', 'Customer', 'Smith']]
					}
				}
			}
		},
		{
			'fieldname': 'party',
			'label': __('Party'),
			'fieldtype': 'Dynamic Link',
			'options': 'party_type',
			/* A Dynamic Link left to itself reads its doctype off the form that is open, which
			   is the form the report was routed from, so the filter is told to read the one beside it. */
			'get_options': function() {
				return frappe.query_report.get_filter_value('party_type')
			}
		},
		{
			'fieldname': 'common_party',
			'label': __('Common Party Account'),
			'fieldtype': 'Check',
			'default': 1,
			//Only a Customer or a Supplier keeps an account that a common party can span
			'depends_on': 'eval:doc.party && ["Customer", "Supplier"].includes(doc.party_type)'
		},
		{
			'fieldname': 'show_cancelled_entries',
			'label': __('Show Cancelled Entries'),
			'fieldtype': 'Check',
			'default': 0
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

// where the charts section remembers whether it was left folded away
const CHARTS_HIDDEN_KEY = 'metal_ledger_charts_hidden'

let hook_purity_chart = function (report) {
	/* The desk draws one chart for a report, and skips its render hooks altogether when the
	   filters leave nothing to show, which would leave the last filters' chart standing. So
	   the purity chart is hung off the refresh that fetched the rows. */
	if (report.purity_chart_hooked) {
		return
	}
	report.purity_chart_hooked = true
	let refresh = report.refresh.bind(report)
	report.refresh = (...args) => {
		// refresh is told whether the filters changed, and answers with the rows it fetched
		return Promise.resolve(refresh(...args)).then(() => update_purity_chart(report))
	}
}

let update_purity_chart = function (report) {
	let $purity_chart = prepare_chart_area(report)
	if (!report.data || !report.data.length) {
		// the rows are gone, and the chart drawn beside this one goes with them
		report.$chart.empty().hide()
	}
	if (!$purity_chart.parent().is(':visible')) {
		// the section is folded away, and the chart is drawn again when it is opened
		return
	}
	frappe.call({
		method: 'aumms.aumms.report.metal_ledger.metal_ledger.get_purity_chart',
		args: { filters: report.get_filter_values() }
	}).then(r => {
		$purity_chart.empty()
		if (!r.message) {
			$purity_chart.hide()
			return
		}
		$purity_chart.show()
		new frappe.Chart($purity_chart[0], Object.assign({
			height: 280,
			axisOptions: {
				shortenYAxisNumbers: 1,
				numberFormatter: frappe.utils.format_chart_axis_number
			}
		}, r.message))
	})
}

let prepare_chart_area = function (report) {
	// the charts share a row, which is looked up rather than built again on each refresh
	let $dashboard = report.page.main.find('.metal-ledger-dashboard')
	if (!$dashboard.length) {
		$dashboard = build_chart_area(report)
	}
	let $charts = $dashboard.find('.metal-ledger-charts')
	if (!$.contains($charts[0], report.$chart[0])) {
		report.$chart.appendTo($charts).css({ flex: '1 1 360px', 'min-width': 0 })
	}
	return $dashboard.find('.purity-chart')
}

let build_chart_area = function (report) {
	let $dashboard = $(`
		<div class="metal-ledger-dashboard">
			<div class="metal-ledger-charts-head" style="display: flex; align-items: center; gap: 4px; padding: 10px 15px 0; cursor: pointer; user-select: none;">
				<span class="charts-caret"></span>
				<span class="text-muted">${__('Charts')}</span>
			</div>
			<div class="metal-ledger-charts" style="display: flex; flex-wrap: wrap;"></div>
		</div>
	`).insertAfter(report.$chart)

	$('<div class="chart-wrapper purity-chart" style="flex: 1 1 360px; min-width: 0;"></div>')
		.appendTo($dashboard.find('.metal-ledger-charts'))
	$dashboard.find('.metal-ledger-charts-head').on('click', () => {
		toggle_charts(report, $dashboard.find('.metal-ledger-charts').is(':visible'))
	})

	// the section opens the way it was last left, on this report alone
	apply_charts_state($dashboard, localStorage.getItem(CHARTS_HIDDEN_KEY) == '1')
	return $dashboard
}

let toggle_charts = function (report, hidden) {
	let $dashboard = report.page.main.find('.metal-ledger-dashboard')
	localStorage.setItem(CHARTS_HIDDEN_KEY, hidden ? '1' : '0')
	apply_charts_state($dashboard, hidden)
	if (!hidden) {
		// a chart drawn into a folded section had no width to draw into, so it is drawn again
		report.chart_options && report.render_chart(report.chart_options)
		update_purity_chart(report)
	}
}

let apply_charts_state = function ($dashboard, hidden) {
	$dashboard.find('.metal-ledger-charts').toggle(!hidden)
	$dashboard.find('.charts-caret')
		.html(frappe.utils.icon(hidden ? 'es-small-right' : 'es-small-down', 'sm'))
}
