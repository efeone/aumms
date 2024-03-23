// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on("Raw Material Bundle", {
	refresh : function(frm) {
    frm.set_query("item_name", "raw_material_details", ()=> {
			return {
				filters: {
					"custom_is_raw_material" : 1
				}
			}
		});
	},
	manufacturing_request: function(frm) {
		if(frm.doc.manufacturing_request) {
			frappe.db.get_value('Manufacturing Request', frm.doc.manufacturing_request, 'quantity')
	    .then(r => {
	        let values = r.message;
					let row = frm.add_child('raw_material_details', {
					    quantity: values.quantity
					});
					frm.refresh_field('raw_material_details');
	    })
		}
	}
});
