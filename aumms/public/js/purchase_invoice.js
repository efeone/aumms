frappe.ui.form.on('Purchase Invoice', {

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
