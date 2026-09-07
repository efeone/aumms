// Copyright (c) 2026, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on("Smith Settlement", {
  refresh: function(frm) {
    frm.set_query("item", () => {
      return {
        filters: {
          "is_purity_item": 1
        }
      };
    });
  },
  smith: function(frm) {
    set_payable_amount(frm);
  },
  manufacturing_request: function(frm) {
    set_payable_amount(frm);
  },
  item: function(frm) {
    //The metal handed over is priced off its own item, not off the piece that was made
    if (!frm.doc.item) {
      return;
    }
    frappe.db.get_value('AuMMS Item', frm.doc.item, ['item_type', 'purity', 'weight_uom'])
      .then(r => {
        if (r.message) {
          frm.set_value('item_type', r.message.item_type);
          frm.set_value('purity', r.message.purity);
          frm.set_value('stock_uom', r.message.weight_uom);
        }
      });
  }
});

/* The app prices nothing a smith does, so the hours worked stand in for a rate. The
   figure is a starting point the user is expected to overwrite with what was agreed. */
function set_payable_amount(frm) {
  if (!frm.doc.smith || !frm.doc.manufacturing_request || frm.doc.payable_amount) {
    return;
  }
  frappe.call({
    method: 'aumms.aumms_manufacturing.doctype.manufacturing_request.manufacturing_request.get_smith_payable',
    args: {
      manufacturing_request: frm.doc.manufacturing_request,
      smith: frm.doc.smith
    },
    callback: function(r) {
      if (r.message) {
        frm.set_value('hours_worked', r.message.hours);
        frm.set_value('hourly_rate', r.message.hourly_rate);
        frm.set_value('payable_amount', r.message.payable_amount);
      }
    }
  });
}
