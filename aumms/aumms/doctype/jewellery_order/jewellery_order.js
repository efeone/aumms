// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on("Jewellery Order", {
    refresh: function(frm) {
        if (!frm.doc.available) {
            frm.add_custom_button('Request for Manufacturing', function() {
                // Add your custom button action here
            }, __('Actions'));
        }
    },
    available: function(frm){
      if (!frm.doc.available) {
          frm.add_custom_button('Request for Manufacturing', function() {
              // Add your custom button action here
          }, __('Actions'));
      }
      else{
        if (frm.doc.available) {
          frm.remove_custom_button('Request for Manufacturing', 'Actions')
        }
      }
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
   }
});
