frappe.ui.form.on('Purchase Order', {
    transaction_date(frm) {
      //Changing the board rate on the changing of transaction_date
      if(frm.doc.posting_date) {
        frm.doc.items.forEach((child) => {
          //call to get board_rate
          set_board_rate(child)
        });
      }
    },

    supplier(frm) {
      //set the supplier type 
      if(frm.doc.supplier) {
        frappe.call({
          method : 'aumms.aumms.doc_events.purchase_order.set_supplier_type',
          args : {
            supplier: frm.doc.supplier
          },
          callback : function(r) {
            if (r.message) {
              frm.doc.items.forEach((child) => {
                child.supplier_type = r.message
              })
            }
          }
        })
      }
    }
});



frappe.ui.form.on('Purchase Order Item', {
  item_code(frm, cdt, cdn) {
    let child = locals[cdt][cdn]
    if (child.item_code) {
      //to make delay in board_rate entry
      setTimeout(function () {
        //call to get board_rate
        set_board_rate(child)
      }, 500);
    }
  },
  board_rate (frm, cdt, cdn) {
    let child = locals[cdt][cdn]
    if (child.board_rate) {
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
  },
items_add(frm, cdt, cdn) {
  if(frm.doc.supplier) {
      set_board_rate_read_only(frm, cdt, cdn)
    }
  }

})

let set_board_rate = function (child) {
   //function to set board rate
   if (child.item_type && child.is_purity_item) {
     frappe.call ({
        method : 'aumms.aumms.utils.get_board_rate',
        args: {
          item_type: child.item_type,
          stock_uom: child.stock_uom,
          date: cur_frm.doc.transaction_date,
          purity: child.purity
        },
        callback : function(r) {
          if (r.message) {
            frappe.model.set_value(child.doctype, child.name, 'board_rate', r.message)
          }
        }
    })
   }
}

let set_board_rate_read_only = function (frm, cdt, cdn) {
  //function for setting supplier type
  let child = locals[cdt][cdn]
    frappe.call({
      method : 'aumms.aumms.doc_events.purchase_order.set_supplier_type',
      args : {
        supplier: frm.doc.supplier
      },
      callback : function(r) {
        if (r.message) {
          child.customer_type = r.message
        }
      }
    })
}
