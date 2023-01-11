frappe.ui.form.on('Sales Invoice Item', {
  item_code: function(frm, cdt, cdn){
    let d = locals[cdt][cdn];
    if (d.item_code){
      frappe.call({
        // Method for fetching  qty, making_charge_percentage, making_charge & board_rate
        method: 'aumms.aumms.doc_events.sales_invoice.get_item_details',
        args: {
          'item_code': d.item_code,
          'item_type': d.item_type,
          'date': frm.doc.posting_date,
          'time': frm.doc.posting_time,
          'purity': d.purity
        },
        callback: function(r) {
          if (r.message){
            d.qty = r.message['qty']
            d.making_charge_percentage = r.message['making_charge_percentage']
            d.making_charge = r.message['making_charge']
            d.board_rate = r.message['board_rate']
            d.making_charge_based_on = r.message ['making_charge_based_on']
          }
        }
      })
    }
  }
})
