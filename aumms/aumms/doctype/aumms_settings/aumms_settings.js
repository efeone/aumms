// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('AuMMS Settings', {
  onload(frm) {
		frm.set_query('metal_ledger_uom', function() {
			return {
				filters: {
					is_purity_uom : 1
				}
			};
		});
	},
});
