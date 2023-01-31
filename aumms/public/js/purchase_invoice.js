frappe.ui.form.on('Purchase Invoice', {

 });

frappe.ui.form.on('Purchase Invoice Item', {
  item_type(frm, cdt, cdn) {
    let child = locals[cdt][cdn]
    if (child.item_type) {
      frappe.call ({
        method: 'aumms.aumms.doc_events.purchase_invoice.check_is_purity_item',
        args: {
          'item_type': child.item_type
        },
        callback: function(r) {
          if (r.message) {
            child.is_purity_item = r.message
          }
          else {
            child.is_purity_item = 0
          }
        }
      })
    }
  },
  items_add(frm, cdt, cdn){
    let child = locals[cdt][cdn]
    //Checking the keep metal ledger
    if(frm.doc.keep_metal_ledger){
      //set value to the field is keep_metal_ledger as 1
      frappe.model.set_value(child.doctype, child.name, 'keep_metal_ledger', 1)
    }
  }

});
