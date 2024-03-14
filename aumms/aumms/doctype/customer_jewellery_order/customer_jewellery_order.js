// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on("Customer Jewellery Order", {
	// refresh(frm) {
  //
	// },
  // validate(frm) {
  //   if(self.total_expected_weight_per_quantity<=self.customer_expected_total_weight)
  //   {
  //
  //   }
  // }
});
frappe.ui.form.on("Customer Jewellery Order Details",{
  expected_weight_per_quantity: function(frm, cdt, cdn){
   let d = locals[cdt][cdn];
   var total_weightage = 0
   frm.doc.order_item.forEach(function(d){
     total_weightage += d.expected_weight_per_quantity * d.item_quantity;
   })
   frm.set_value('total_expected_weight_per_quantity',total_weightage)
 },
 order_item_remove:function(frm){
     var total_weightage = 0
     frm.doc.order_item.forEach(function(d){
       total_weightage += d.expected_weight_per_quantity;
     })
     frm.set_value("total_expected_weight_per_quantity",total_weightage)
   }
})
