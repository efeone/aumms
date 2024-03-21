// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on("Raw Material Required", {
  setup(frm) {
    set_filters(frm);
  },
  validate: function(frm) {
    if (!frm.is_new()) {
      frm.set_df_property('raw_material_required_date', 'reqd', 1);
    }
  }
});


frappe.ui.form.on("Raw Material Details", {
  quantity: function (frm, cdt, cdn) {
    let d = locals[cdt][cdn];
    var total_weightage = 0;
    frm.doc.raw_materials.forEach(function (d) {
      total_weightage += d.weight * d.quantity;
    });
    frm.set_value("total_raw_material_weight", total_weightage);
  },
  raw_materials_remove: function (frm, cdt, cdn) {
    var total_weightage = 0;
    frm.doc.raw_material_details.forEach(function (d) {
      total_weightage += d.weight * d.quantity;
    });
    frm.set_value("total_raw_material_weight", total_weightage);
  },
  weight: function (frm, cdt, cdn) {
    let d = locals[cdt][cdn];
    var total_weightage = 0;
    frm.doc.raw_materials.forEach(function (d) {
      total_weightage += d.weight * d.quantity;
    });
    frm.set_value("total_raw_material_weight", total_weightage);
  },
});

let set_filters = function(frm){
  frm.set_query('item_name','raw_materials',() => {
    return {
      filters: {
        "is_raw_material": 1
      }
    };
  });
}
