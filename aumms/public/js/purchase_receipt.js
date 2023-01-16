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
  }
});

//declare board_rate
let board_rate;

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
      board_rate = 0
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

                board_rate = r.message
                if (child.conversion_factor) {
                  //change rate in accordance with conversion_factor
                  board_rate = board_rate * child.conversion_factor
                }
                //set value to rate field
                frappe.model.set_value(child.doctype, child.name, 'rate', board_rate)

            }
          }
        })
      }, 500);
    }

  },
  conversion_factor (frm, cdt, cdn) {
    let child = locals[cdt][cdn]

    if (!board_rate) {
      // change board rate as rate
      board_rate = child.rate
    }
    if (child.conversion_factor) {

      let rate = board_rate * child.conversion_factor
      //set value to rate field
      frappe.model.set_value(child.doctype, child.name, 'rate', rate)

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
