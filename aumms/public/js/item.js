frappe.ui.form.on('Item', {
  refresh(frm) {
    if(frm.doc.is_aumms_item){
      frm.disable_form()
      frm.disable_save()
    }
  }
})
