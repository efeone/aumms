// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on("Purchase Tool", {
    // refresh : function(frm){}
});

frappe.ui.form.on("Purchase Item Details",{
    item_details_add : function(frm, cdt, cdn){
        let child = locals[cdt][cdn]
        if(frm.doc.stone){
            frappe.model.set_value(child.doctype, child.name, 'stone', frm.doc.stone);
        }
    }
});
