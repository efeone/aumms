// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Design Request', {

	// Delivery date valdation 
	delivery_date: function(frm){
		if (frm.doc.delivery_date < frappe.datetime.get_today()){
			frm.set_value('delivery_date', null)
			frappe.throw(__('Delivery date cannot be in the past'))
		}
	}
});






