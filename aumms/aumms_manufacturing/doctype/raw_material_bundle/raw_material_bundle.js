// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on("Raw Material Bundle", {
  refresh: function(frm) {
    frm.set_query("item", "items", () => {
      return {
        filters: {
          "custom_is_raw_material": 1
        }
      };
    });
    add_view_buttons(frm);
    /* A short bundle cannot be submitted, so the request for the shortage is raised
       from the draft, and the button goes once the stock is in. */
    if (!frm.is_new() && frm.doc.docstatus === 0 && !frm.doc.raw_material_available) {
      frm.add_custom_button('Create Raw Material Request', () => {
        frappe.call({
          method: 'aumms.aumms_manufacturing.doctype.raw_material_bundle.raw_material_bundle.create_raw_material_request',
          args: {
            docname: frm.doc.name
          },
          freeze: true,
          callback: (r) => {
            frm.reload_doc();
          }
        });
      });
    }
  },
  source_warehouse: function(frm) {
    //The bundle is picked from one warehouse, so the rows follow it
    (frm.doc.items || []).forEach(row => {
      frappe.model.set_value(row.doctype, row.name, 'warehouse', frm.doc.source_warehouse);
    });
  }
});

frappe.ui.form.on("Raw Material Details", {
  items_add: function(frm, cdt, cdn) {
    frappe.model.set_value(cdt, cdn, 'warehouse', frm.doc.source_warehouse);
  },
  item: function(frm, cdt, cdn) {
    set_available_stock(frm, cdt, cdn);
  },
  warehouse: function(frm, cdt, cdn) {
    set_available_stock(frm, cdt, cdn);
  }
});

/* What the warehouse already holds is filled in for the user, and left editable so a
   count that disagrees with the system can be keyed in before the bundle is submitted. */
function set_available_stock(frm, cdt, cdn) {
  let row = locals[cdt][cdn];
  if (!row.item || !row.warehouse) {
    return;
  }
  frappe.call({
    method: 'aumms.aumms_manufacturing.doctype.raw_material_bundle.raw_material_bundle.get_available_stock',
    args: {
      item: row.item,
      warehouse: row.warehouse
    },
    callback: function(r) {
      if (r.message) {
        frappe.model.set_value(cdt, cdn, 'available_quantity', r.message.available_quantity);
        frappe.model.set_value(cdt, cdn, 'available_weight', r.message.available_weight);
      }
    }
  });
}

/* Both documents are written on submit, so they are reached from the bundle that wrote
   them. A bundle of nothing but non metal rows has no ledger, and gets no button. */
function add_view_buttons(frm) {
  if (frm.doc.docstatus !== 1) {
    return;
  }
  if (frm.doc.stock_entry) {
    frm.add_custom_button(__('Stock Entry'), () => {
      frappe.set_route('Form', 'Stock Entry', frm.doc.stock_entry);
    }, __('View'));
  }
  let metal_ledger_filters = {
    voucher_type: 'Raw Material Bundle',
    voucher_no: frm.doc.name
  };
  frappe.db.count('Metal Ledger Entry', { filters: metal_ledger_filters }).then(count => {
    if (count) {
      frm.add_custom_button(__('Metal Ledger'), () => {
        /* The report reads the entries as a ledger, with the running balance and the
           purity conversion the raw list cannot show. Its date range is mandatory, so it
           opens around the day the bundle posted. */
        let posting_date = frm.doc.posting_date || frappe.datetime.get_today();
        frappe.set_route('query-report', 'Metal Ledger', Object.assign({}, metal_ledger_filters, {
          from_date: frappe.datetime.add_months(posting_date, -1),
          to_date: frappe.datetime.add_months(posting_date, 1)
        }));
      }, __('View'));
    }
  });
}
