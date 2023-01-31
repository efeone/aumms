// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Board Rate', {
	onload(frm) {
		frm.set_query('uom', function() {
			return {
				filters: {
					is_purity_uom : 1
				}
			};
		});
	},
	validate(frm){
		set_title_name(frm)
	}
});
function set_title_name(frm){//set title for board_rate
	frm.set_value('title', frm.doc.item_type + '-' + frm.doc.purity + '-' + frm.doc.board_rate);
}
