frappe.ui.form.on('Purchase Receipt', {
  is_metal_transaction (frm) {
    //Check is metal transaction
    if(frm.doc.is_metal_transaction){
      change_is_metal_transaction(frm, 1)
    }
    else{
      change_is_metal_transaction(frm, 0)
    }
    frm.refresh_field('items')
  }
});

frappe.ui.form.on('Purchase Receipt Item',{
  items_add(frm, cdt, cdn){
    let child = locals[cdt][cdn]
    //Check is metal transaction
    if(frm.doc.is_metal_transaction){
      //set value to the field is is_metal_transaction as 1
      frappe.model.set_value(child.doctype, child.name, 'is_metal_transaction', 1)
    }
  }

});


let change_is_metal_transaction = function (frm, value){
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
