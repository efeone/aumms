frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Board Rate by Purity"] = {
	method: "aumms.aumms.dashboard_chart_source.board_rate_by_purity.board_rate_by_purity.get",
	filters: [
		{
			fieldname: "item_type",
			label: __("Item Type"),
			fieldtype: "Link",
			options: "Item Type",
			get_query: () => {
				return { filters: { is_purity_item: 1 } };
			},
		},
	],
};
