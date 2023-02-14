// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Board Rate', {
	onload(frm) {
		set_filter('uom', {is_purity_uom: 1})
		set_filter('item_type', {is_purity_item: 1})
	},
	validate(frm) {
		set_title_name(frm)
	}
});
function set_title_name(frm) {//set title for board_rate
	frm.set_value('title', frm.doc.item_type + '-' + frm.doc.purity + '-' + frm.doc.board_rate);
}

let set_filter = function (field, filters) {
	/*
		function to set filter for a specific field
		args:
			field: field name
			filters: set of filters, (eg: {key:value})
		output: filter applied list for field
	*/
	cur_frm.set_query(field, () => {
	  return {
		filters: filters
	  }
	})
  }