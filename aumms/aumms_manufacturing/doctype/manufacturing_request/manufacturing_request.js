// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on("Manufacturing Request", {
  refresh: function(frm) {
		frm.set_query('uom',()=>{
			return {
				filters: {
					"is_purity_uom": 1
				}
			}
		});
  },
  });
  frappe.ui.form.on("Manufacturing Request Stage", {
    select_raw_material: function(frm) {
      frappe.new_doc('Raw Material Bundle', {
        'manufacturing_request': frm.doc.name,
        'raw_material_details': [
          {
            'quantity': frm.doc.quantity
          }
        ]
      })
    }
});
