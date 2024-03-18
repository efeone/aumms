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
		 frm.set_df_property('design_attachment', 'read_only', 1)
   }
 },
  available_quantity_in_stock: function(frm) {
    limit_item_details(frm)
  }
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
   item_details_add: function(frm)  {
    limit_item_details(frm)
   }
});

function limit_item_details(frm) {
	if(frm.doc.quantity >= frm.doc.available_quantity_in_stock){
		limit = frm.doc.quantity - frm.doc.available_quantity_in_stock
	}
	else if(frm.doc.quantity <= frm.doc.available_quantity_in_stoc){
		limit = frm.doc.quantity
	}
  if (frm.doc.item_details.length >= limit)  {
    $(".btn.btn-xs.btn-secondary.grid-add-row").hide();
  }
  else  {
    $(".btn.btn-xs.btn-secondary.grid-add-row").show();
  }
}
