// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on("Jewellery Order", {
	// refresh(frm) {
  //
	// },
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
   }
});
