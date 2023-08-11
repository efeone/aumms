frappe.ui.form.on('Item Group', {
  refresh(frm) {
    if(frm.doc.is_aumms_item_group){
      frm.disable_form()
      frm.disable_save()
    }
  }
});
