// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Design Request', {
    setup:function(frm){
        frm.set_query('unit_of_measure', 'design_details', ()=> {
            return{
                filters: {
                    "is_purity_uom":1
                }
            }
        });
    },
	// Delivery date valdation 
	delivery_date: function(frm){
		if (frm.doc.delivery_date < frappe.datetime.get_today()){
			frm.set_value('delivery_date', )
			frappe.throw(__('Delivery date cannot be in the past'))
		}
	},
	refresh: function(frm) {
        if(!frm.doc.assigned_person && !frm.is_new() && frm.doc.docstatus == 1) {
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
                                    d.set_value('assign_to', frappe.session.user); // Clear value when Self Assign is checked
                                }
                            }
                        },
                        {
                            fieldtype: 'Link',
                            label: 'Assign To',
                            fieldname: 'assign_to',
                            options: 'User',
                            get_query: function () {
                                return {
                                    query : 'aumms.aumms.doctype.design_request.design_request.design_analyst_user_query',
                                };
                            },
                            depends_on: 'eval: !doc.self_assign' // Show the field only when Self Assign is not checked
                        }
                    ],
                    primary_action_label: __('Submit'),
                    primary_action(values) {
                        let assign_to = '';
                        if(values.self_assign){
                            assign_to = frappe.session.user;
                        }
                        else{
                            assign_to = values.assign_to;
                        }
                        frappe.call({
                            method: 'aumms.aumms.doctype.design_request.design_request.assign_design_request',
                            args: {
                                doctype: frm.doc.doctype,
                                docname: frm.doc.name,
                                assign_to: assign_to
                            },
                            freeze: true,
                            callback: (r) => {
                                frm.reload_doc();
                                d.hide()
                            }
                        });
                    }
                });
                // Show the dialog                
                d.show();
            });
        }   
    }
});






