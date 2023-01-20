frappe.ui.form.on('Purchase Invoice', {
  keep_metal_ledger (frm) {
    //Checking the keep metal ledger
    if(frm.doc.keep_metal_ledger){
      change_keep_metal_ledger(frm, 1)
    }
    else{
      change_keep_metal_ledger(frm, 0)
    }
    frm.refresh_field('items')
  }
});

frappe.ui.form.on('Purchase Invoice Item',{
  items_add(frm, cdt, cdn){
    let child = locals[cdt][cdn]
    //Checking the keep metal ledger
    if(frm.doc.keep_metal_ledger){
      //set value to the field is keep_metal_ledger as 1
      frappe.model.set_value(child.doctype, child.name, 'keep_metal_ledger', 1)
    }
  }

});


let change_keep_metal_ledger = function (frm, value){
  /*
    function to iterate item table and set value to the field keep_metal_ledger
    args:
      frm: current form of purchase Invoice
      value: Boolean
  */
  frm.doc.items.forEach((item) => {
    item.keep_metal_ledger = value
  });
}
