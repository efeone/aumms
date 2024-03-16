// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on("Jewellery Order", {
	refresh(frm) {
    if (!frm.is_new()){
     frm.set_df_property('customer_jewellery_order', 'read_only', 1)
     frm.set_df_property('customer', 'read_only', 1)
     frm.set_df_property('required_date', 'read_only', 1)
     frm.set_df_property('customer_expected_total_weight', 'read_only', 1)
     frm.set_df_property('customer_expected_amount', 'read_only', 1)
     frm.set_df_property('total_weight', 'read_only', 1)
     frm.set_df_property('quantity', 'read_only', 1)
   }
	},
});

frappe.ui.form.on("Jewellery Order Items",{
  weight: function(frm, cdt, cdn){
   let d = locals[cdt][cdn];
   var total_weightage = 0
   frm.doc.item_details.forEach(function(d){
     total_weightage += d.weight;
   })
   frm.set_value('total_weight',total_weightage)
 },
 item_details_remove:function(frm){
     var total_weightage = 0
     frm.doc.item_details.forEach(function(d){
       total_weightage += d.weight;
     })
     frm.set_value("total_weight",total_weightage)
   },
});
