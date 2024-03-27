// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on("Raw Material Request", {
  setup : function(frm){
    frm.set_query('uom', ()=>{
      return{
        filters :{
          "is_purity_uom" : 1
        }
      }
    })
  },
  refresh :function(frm){
    if (frm.doc.not_available) {
      frm.add_custom_button(__('Issue Raw Material'), function ()
      {
            // frm.trigger("create_manufacturing_request");
      }, __("Action"));
      frm.add_custom_button(__('Manufacturing Request'), function ()
      {
        frm.call('create_manufacturing_request').then(r => {
          frm.refresh_fields();
        });
      }, __("Action"));
      frm.add_custom_button(__('Purchase Order'), function ()
      {
        frm.call('create_purchase_order').then(r => {
          frm.refresh_fields();
        });
      }, __("Action"));
    }
  }
});
