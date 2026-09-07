// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('AuMMS Settings', {
	setup(frm) {
		set_filters(frm);
	},
});

function set_filters(frm) {
	frm.set_query('metal_ledger_uom', function() {
		return {
			filters: {
				is_purity_uom : 1
			}
		};
	});
	frm.set_query('purity_uom', function() {
		return {
			filters: {
				is_purity_uom : 1
			}
		};
	});
}
