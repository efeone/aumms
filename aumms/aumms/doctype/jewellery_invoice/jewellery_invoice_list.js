// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.listview_settings['Jewellery Invoice'] ={
  add_fields: ["customer_name", "status", "delivery_date", "grand_total", "name"],
  has_indicator_for_draft: 1,
  get_indicator: function(doc) {
    const status_colors = {
      "Estimate": "grey",
      "Ordered": "orange",
      "Advance Received": "purple",
      "Invoiced": "yellow",
      "Delivered": "green",
      "Unpaid": "red",
      "Paid": "green",
      "Partly Paid": "blue",
      "Overdue": "red"
    };
		return [__(doc.status), status_colors[doc.status], "status,=,"+doc.status];
	},
};
