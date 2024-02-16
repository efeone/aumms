// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on("Purchase Tool", {

    // refresh : function(frm){}

});

frappe.ui.form.on("Purchase Item Details", {
    item_details_add: function(frm, cdt, cdn) {
        let child = locals[cdt][cdn];
        if (frm.doc.stone) {
            frappe.model.set_value(child.doctype, child.name, 'stone', frm.doc.stone);
        }
    },
    stone_weight: function(frm, cdt, cdn) {
        let d = locals[cdt][cdn];
        if (frm.doc.has_stone) {
            let net_weight = d.gold_weight + d.stone_weight;
            frappe.model.set_value(cdt, cdn, 'net_weight', net_weight);
        }
    },
    gold_weight: function(frm, cdt, cdn) {
        let d = locals[cdt][cdn];
        if (!frm.doc.has_stone) {
            frappe.model.set_value(cdt, cdn, 'net_weight', d.gold_weight);
        }
    },
});
