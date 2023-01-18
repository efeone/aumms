frappe.ui.form.on('Purchase Receipt', {
  is_metal_transaction(frm) {
    //Check is metal transaction
    if (frm.doc.is_metal_transaction) {
      change_is_metal_transaction(frm, 1)
    }
    else {
      change_is_metal_transaction(frm, 0)
    }
    frm.refresh_field('items')
  },
  refresh (frm) {

    if ([1, 2].includes(frm.doc.docstatus)) {

      // Custom button Metal Ledger in View
      frm.add_custom_button('Metal Ledger', () => {
        // route to Metal Ledger Report with filter of this voucher no
        frappe.set_route('query-report', 'Metal Ledger', { 'voucher_no': frm.doc.name });
      }, 'View');

    }

  }
});

frappe.ui.form.on('Purchase Receipt Item', {
  items_add(frm, cdt, cdn) {
    let child = locals[cdt][cdn]
    //Check is metal transaction
    if (frm.doc.is_metal_transaction) {
      //set value to the field is is_metal_transaction as 1
      frappe.model.set_value(child.doctype, child.name, 'is_metal_transaction', 1)
    }
  },
  item_code(frm, cdt, cdn) {
    let child = locals[cdt][cdn]

    if (child.item_code) {
      //to make delay in board_rate entry
      setTimeout(function () {
        //call to get board_rate
        frappe.call({
          method: 'aumms.aumms.utils.get_board_rate',
          args: {
            item_code: child.item_code,
            item_type: child.item_type,
            date: frm.doc.posting_date,
            time: frm.doc.posting_time,
            purity: child.purity
          },
          callback: function (r) {
            if (r.message) {

              //set value to rate field
              frappe.model.set_value(child.doctype, child.name, 'board_rate', r.message)

            }
          }
        })
      }, 500);
    }

  },
  board_rate (frm, cdt, cdn) {
    let child = locals[cdt][cdn]

    if (child.board_rate){
      // declare rate value as board rate
      let rate = child.board_rate
      if (child.conversion_factor) {
        // multiply rate with conversion factor
        rate = rate * child.conversion_factor
      }
      // set value to the rate field
      frappe.model.set_value(child.doctype, child.name, 'rate', rate)
    }

  },
  conversion_factor (frm, cdt, cdn) {
    let child = locals[cdt][cdn]

    if (child.conversion_factor) {
      // trigger board rate field
      frm.script_manager.trigger('board_rate', cdt, cdn);
    }

  }
})

let change_is_metal_transaction = function (frm, value) {
  /*
    function to iterate item table and set value to the field is_metal_transaction
    args:
      frm: current form of purchase Receipt
      value: Boolean
  */
  frm.doc.items.forEach((item) => {
    item.is_metal_transaction = value
  });
}
