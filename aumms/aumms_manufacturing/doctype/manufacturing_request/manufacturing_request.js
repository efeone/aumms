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
  select_raw_material: function(frm) {
    frappe.model.open_mapped_doc({
        method: "aumms.aumms_manufacturing.doctype.manufacturing_request.manufacturing_request.create_required_raw_material",
        source_name: frm.doc.name,
        frm: cur_frm
    });
}
});
