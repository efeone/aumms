// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on("Customer Jewellery Order", {
	refresh(frm) {
    if (!frm.is_new()){
      frm.add_custom_button('Jewellery Order', () => {
        frappe.call('aumms.aumms.doctype.customer_jewellery_order.customer_jewellery_order.create_jewellery_order', {
          customer_jewellery_order : frm.doc.name
        }).then(r =>{
            frm.reload_doc();
        });
      },'Create');
    }
	},
});
