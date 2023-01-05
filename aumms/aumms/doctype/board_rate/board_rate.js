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
	}
});
