// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on("Purchase Tool", {
	is_stone(frm) {
    if(frm.doc.is_stone == 1){
      frm.set_df_property("has_stone", "hidden", 1)
    }
    else{
      frm.set_df_property("has_stone", "hidden", 0)
    }
	},
  has_stone(frm){
    if(frm.doc.has_stone == 1){
      frm.set_df_property("is_stone", "hidden", 1)
    }
    else{
      frm.set_df_property("is_stone", "hidden", 0)
    }
  }
});
