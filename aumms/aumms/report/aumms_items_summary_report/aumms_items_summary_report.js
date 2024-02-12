// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt

frappe.query_reports["Aumms Items Summary report"] = {
	"filters": [

			{
					"label":__("Item Group"),
					"fieldname":"item_group",
					"fieldtype":"Link",
					"options":"AuMMS Item Group"
			},
			{
					"label":__("Item Code"),
					"fieldname":"item_code",
					"fieldtype":"Data",
			},

	]
};
