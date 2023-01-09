frappe.ui.form.on('Sales Invoice Item', {
  item_code:function(frm, cdt, cdn){
    let d = locals[cdt][cdn];
    if (d.item_code){
      frappe.call({//function for qty, making_charge_percentage, making_charge & board_rate fetching
        method:'aumms.aumms.doc_events.sales_invoice.fetch_qty',
        args:{
          'item':d.item_code,
          'type':d.item_type
        },
        callback: function(r) {
          if (r.message[0]){
            d.qty=r.message[0]
          }
          if (r.message[1]){
            d.making_charge_percentage=r.message[1]
          }
          if (r.message[2]){
            d.making_charge=r.message[2]
          }
          if (r.message[3]){
            d.board_rate=r.message[3]
          }
        }
      })
    }
  }
})
