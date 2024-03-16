// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on("Customer Jewellery Order", {
  customer_expected_total_weight: function (frm) {
    calculate_customer_expected_amount(frm);
  },
  uom: function (frm) {
    calculate_customer_expected_amount(frm);
  },
  purity: function (frm) {
    calculate_customer_expected_amount(frm);
  },
});

frappe.ui.form.on("Customer Jewellery Order Details", {
  expected_weight_per_quantity: function (frm, cdt, cdn) {
    let d = locals[cdt][cdn];
    var total_weightage = 0;
    frm.doc.order_item.forEach(function (d) {
      total_weightage += d.expected_weight_per_quantity * d.item_quantity;
    });
    frm.set_value("total_expected_weight_per_quantity", total_weightage);
  },

  order_item_remove: function (frm) {
    var total_weightage = 0;
    frm.doc.order_item.forEach(function (d) {
      total_weightage += d.expected_weight_per_quantity;
    });
    frm.set_value("total_expected_weight_per_quantity", total_weightage);
  },
});

function calculate_customer_expected_amount(frm) {
  if (frm.doc.customer_expected_total_weight && frm.doc.uom && frm.doc.purity) {
    board_rate = frm.call("calculate_customer_expected_amount");
  }
}
