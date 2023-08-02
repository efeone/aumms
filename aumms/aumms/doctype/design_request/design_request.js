// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Design Request', {

	// Delivery date valdation 
	delivery_date: function(frm){
		if (frm.doc.delivery_date < frappe.datetime.get_today()){
			frm.set_value('delivery_date', null)
			frappe.throw(__('Delivery date cannot be in the past'))
		}
	},
	refresh: function(frm) {
        frm.add_custom_button(__('Assign'), () => {
            let d = new frappe.ui.Dialog({
                title: __('Assign Design Request'),
                fields: [
                    {
                        fieldtype: 'Check',
                        label: 'Self Assign',
                        fieldname: 'self_assign',
                        default: 0,
                        onchange: function(e) {
                            d.toggle_enable('assign_to', !e.checked);
                            if (e.checked) {
                                d.set_value('assign_to', null); // Clear value when Self Assign is checked
                            }
                        }
                    },
                    {
                        fieldtype: 'Link',
                        label: 'Assign To',
                        fieldname: 'assign_to',
                        options: 'Role',
                        depends_on: 'eval: !doc.self_assign' // Show the field only when Self Assign is not checked
                    }
                ],
                primary_action_label: __('Submit'),
                primary_action(values) {
					console.log(values.self_assign);
					console.log(values.assign_to);
                    // Optional: Show a message after the form fields are updated
                    frappe.msgprint(__('Design Request has been assigned.'));

                    // Close the dialog after submitting
                    d.hide();
                }
            });

            // Show the dialog
            d.show();
        });
    }
});






