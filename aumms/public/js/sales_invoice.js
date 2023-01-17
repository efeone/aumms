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
            d.is_fixed_making_charge = r.message['making_charge']
            d.board_rate = r.message['board_rate']
            d.making_charge_based_on = r.message ['making_charge_based_on']
            d.amount_with_out_making_charge = r.message['qty'] * r.message['board_rate']
            setTimeout(() => {
             frappe.model.set_value(d.doctype, d.name, 'rate', (d.amount_with_out_making_charge + d.making_charge)/d.qty)// set time out of 500 ms for  rate
           }, 500);
            if (r.message['making_charge']){
              d.making_charge = r.message['making_charge']
            }
            else {
                d.making_charge = (d.amount_with_out_making_charge)*(d.making_charge_percentage * 0.01)//set making_charge if it's percentage
              }
          }
        }
      })
    }
  },
  qty: function(frm, cdt, cdn){

    let d = locals[cdt][cdn];
    if (d.qty){
      frappe.model.set_value(d.doctype, d.name, 'amount_with_out_making_charge', d.qty * d.board_rate);//set amount_with_out_making_charge while changing qty

    }
  },
  making_charge_percentage: function(frm, cdt, cdn){

    let d = locals[cdt][cdn];
    if (d.making_charge_percentage){
      var making_charge = d.amount_with_out_making_charge * d.making_charge_percentage * 0.01
      frappe.model.set_value(d.doctype, d.name, 'making_charge', making_charge);//set making_charge while changing of making_charge_percentage
    }
    frm.refresh_field('items')
  },
  amount_with_out_making_charge: function(frm, cdt, cdn){

    let d = locals[cdt][cdn];
    if (d.amount_with_out_making_charge){
      var making_charge = d.amount_with_out_making_charge * d.making_charge_percentage * 0.01
      frappe.model.set_value(d.doctype, d.name, 'making_charge', making_charge);//set making_charge while changing of amount_with_out_making_charge
    }
    frm.refresh_field('items')
  },
  making_charge:function (frm, cdt, cdn) {

    let d = locals[cdt][cdn];
    if(d.making_charge) {
      let rate = (d.amount_with_out_making_charge + d.making_charge)/d.qty
      if (rate)
      {
        frappe.model.set_value(d.doctype, d.name, 'rate', rate);//set rate by the change of making_charge
      }
    }
  },
  amount_with_out_making_charge:function (frm, cdt, cdn) {

    let d = locals[cdt][cdn];
    if(d.amount_with_out_making_charge) {
      let rate = (d.amount_with_out_making_charge + d.making_charge)/d.qty
      if (rate)
      {
        frappe.model.set_value(d.doctype, d.name, 'rate', rate);//set rate by the change of amount_with_out_making_charge
      }
    }
  },
  conversion_factor:function(frm, cdt,cdn){

    let d = locals[cdt][cdn];
    if(d.conversion_factor){
      var rate = d.board_rate * d.conversion_factor
      frappe.model.set_value(d.doctype, d.name, 'rate', rate);//set rate by the change of conversion_factor
    }
  }
})
