
frappe.ui.form.on('Purchase Request', {
    refresh: function(frm) {
        frm.add_custom_button(__('Create Purchase Order'), function() {
            frappe.call({
                method: 'aumms.aumms_manufacturing.doctype.purchase_request.purchase_request.create_purchase_order',
                args :{
                  purchase_request: frm.doc.name
                },
                callback: function(r) {
                  frm.refresh();
                }
            });
        });
    }
});
