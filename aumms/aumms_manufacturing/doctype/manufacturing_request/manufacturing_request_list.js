// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt

/* Draft and Cancelled are returned before the indicator is asked for on a submittable
   doctype, so both are claimed here for the request to read as its own status. */
frappe.listview_settings['Manufacturing Request'] = {
	add_fields: ['status'],
	has_indicator_for_draft: 1,
	has_indicator_for_cancelled: 1,
	get_indicator: function(doc) {
		const status_colors = {
			'Pending': 'grey',
			'Manufacturing': 'orange',
			'Manufactured': 'blue',
			'Completed': 'green',
			'Cancelled': 'red'
		};
		if (!doc.status) {
			return;
		}
		return [__(doc.status), status_colors[doc.status], 'status,=,' + doc.status];
	}
};
