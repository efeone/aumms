// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on("Jewellery Receipt", {
  refresh:function(frm) {

    // show only customers whose territory is set to India
    frm.set_query('stone', () => {
        return {
            filters: {
                is_stone_item: 1
            }
        }
    })

  },
});

frappe.ui.form.on("Jewellery Item Receipt", {
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
        let net_weight = d.gold_weight;
        frappe.model.set_value(cdt, cdn, 'net_weight', net_weight);
        let amount = d.gold_weight * frm.doc.board_rate;
        frappe.model.set_value(cdt, cdn, 'amount', amount);
      }
    },
    stone_charge: function(frm, cdt, cdn) {
        let d = locals[cdt][cdn];
        if (frm.doc.has_stone) {
            let amount = (d.gold_weight * frm.doc.board_rate) + (d.stone_charge);
            frappe.model.set_value(cdt, cdn, 'amount', amount);
        }
    }
});
