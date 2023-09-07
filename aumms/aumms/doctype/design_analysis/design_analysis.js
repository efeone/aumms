// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Design Analysis', {
    setup:function(frm){
        frm.set_query('unit_of_measure', 'verified_item', ()=> {
      return{
        filters: {
          "is_purity_uom":1
        }
      }
    });
        frm.set_query('unit_of_measure', 'design_details', ()=> {
      return{
        filters: {
            "is_purity_uom":1
        }
      }      
    });
	},
    design_request: function(frm) {
        // Clear existing rows in the "Design Details" table
        frm.clear_table('design_details');

        // Fetch data from the "Design Details" child table of the linked "Design Request"
        if (frm.doc.design_request) {
            frappe.call({
                method: 'aumms.aumms.doctype.design_analysis.design_analysis.fetch_design_details',
                args: {
                    parent: frm.doc.design_request
                },
                callback: function(response) {
                    if (response.message && response.message.length > 0) {
                        // Add rows to the "Design Details" table based on the fetched data
                        response.message.forEach(function(detail) {
                            let row = frappe.model.add_child(frm.doc, 'Design Details', 'design_details');
                            row.material = detail.material;
                            row.item_type = detail.item_type;
                            row.purity = detail.purity;
                            row.unit_of_measure = detail.unit_of_measure;
                            row.quantity = detail.quantity;
                            row.is_customer_provided = detail.is_customer_provided;
                        });

                        frm.refresh_field('design_details');
                    }
                }
            });
        }
    },
    refresh: function(frm) {
        frm.add_custom_button('Request For Approval', () => {
            console.log("Refresh");
        let dia = new frappe.ui.Dialog({
            title: __('Request for Approval'),
            fields: [
                {
                    fieldtype: 'Check',
                    label: 'Self Approval',
                    fieldname: 'self_approval',
                    default: 0,
                    onchange: function() {
                        dia.toggle_enable('assign_to', !this.value);
                        if (this.value) {
                            dia.set_value('assign_to', null); // Clear value when Self Assign is checked
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
                            query : 'aumms.aumms.doctype.design_analysis.design_analysis.supervisor_user_query',
                        };
                    },
                    depends_on: 'eval: !doc.self_approval'
                }
            ],
            primary_action_label: __('Submit'),
            //primary_action: function() {
            //    const values = dia.get_values();
              //  console.log(values.self_approval);
                //console.log(values.assign_to);
            primary_action(values) {
                let assign_to = '';
                if(values.self_assign){
                    assign_to = frappe.session.user;
                }
                else{
                    assign_to = values.assign_to;
                }
                frappe.call({
                    method: 'frappe.desk.form.assign_to.add',
                    args: {
                        doctype: frm.doc.doctype,
                        name: frm.doc.name,
                        assign_to: [assign_to]
                    },
                    freeze: true,
                    callback: (r) => {
                        console.log(r)
                    },
                })
                // Update the button text after successful assignment
                let assignButton = document.getElementById('assignButton');
                assignButton.textContent = 'Assigned';
                // Optional: Show a message after the form fields are updated
                frappe.msgprint(__('Design Analysis has been approved.'));
                // Close the dialog after submitting
                dia.hide();
            }
        });

        // Show the dialog
        dia.show();
        });
        // Check if the logged-in user is a supervisor
        const isSupervisor = frappe.user_roles.includes('Supervisor');
    if (isSupervisor) {
        frm.add_custom_button(__('Approve'), () => {
            const item_code = frm.doc.item_code;
            const item_group = frm.doc.item_group;
            const purity = frm.doc.purity;

            frappe.call({
                method: 'aumms.aumms.doctype.design_analysis.design_analysis.create_aumms_item_from_design_analysis',
                args: {
                    item_code: item_code,
                    item_group: item_group,
                    purity: purity
                },
                callback: (r) => {
                    if (r.message) {
                        console.log('AuMMS Item Created:', r.message);
                    } else {
                        console.log('Failed to create AuMMS Item');
                    }
                }
            });

            frappe.call({
                method: 'aumms.aumms.doctype.design_analysis.design_analysis.create_design_request_from_design_analysis',
                args: {
                    customer_name: customer,
                    mobile_number: mobile_no,
                    'self.design_details[0].Material': design_title,
                    delivery_date: delivery_date,
                    'self.design_details[0].Attachment': attachment
                },
                callback: (r) => {
                    if (r.message) {
                        console.log('Design Request Created:', r.message);
                    } else {
                        console.log('Failed to Create Design Request');
                    }
                }
            });
        });
        }
    }
});
