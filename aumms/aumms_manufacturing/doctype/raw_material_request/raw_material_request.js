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
  }
});
