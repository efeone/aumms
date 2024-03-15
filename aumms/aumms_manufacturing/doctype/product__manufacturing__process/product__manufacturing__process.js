// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Product  Manufacturing  Process", {
// 	refresh(frm) {

// 	},
// });


frappe.ui.form.on("Product Manufacturing Process", {
  setup : function(frm){
    frm.set_query('assign_to', ()=>{
      return{
        filters :{
          "smith" : 1
        }
      }
    })
  }
});
