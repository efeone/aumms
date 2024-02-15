// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on("Purchase Tool", {
    refresh : function(frm){
        if(frm.doc.has_stone == 1){
             frm.fields_dict.item_details.grid.update_docfield_property('stone', 'hidden', 1);
             frm.fields_dict.item_details.grid.update_docfield_property('stone_weight', 'hidden', 1);
             frm.fields_dict.item_details.grid.update_docfield_property('stone_charge', 'hidden', 1);
        }
        else{
            frm.fields_dict.item_details.grid.update_docfield_property('stone', 'hidden', 0);
            frm.fields_dict.item_details.grid.update_docfield_property('stone_weight', 'hidden', 0);
            frm.fields_dict.item_details.grid.update_docfield_property('stone_charge', 'hidden', 0);
        }
    }
});

frappe.ui.form.on("Purchase Item Details",{
    item_details_add : function(frm, cdt, cdn){
        let child = locals[cdt][cdn]
        if(frm.doc.stone){
            frappe.model.set_value(child.doctype, child.name, 'stone', frm.doc.stone);
        }
    }
});
