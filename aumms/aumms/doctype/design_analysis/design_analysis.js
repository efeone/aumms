// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Design Analysis', {
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
            // frappe.new_doc('Library Membership', {
                // library_member: frm.doc.name
            // })
        })
    }
});
