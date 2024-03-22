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
		if(frm.doc.manufacturing_request){
			frappe.call({
				method : 'aumms.aumms_manufacturing.doctype.raw_material_bundle.raw_material_bundle.show_raw_materiel_request_name',
				args :{
					doc : frm.doc.name
				},
				callback : function(r){
					frm.refresh_fields()
				}

			})
		}

	},
});
