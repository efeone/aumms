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
    refresh: function(frm){
      create_custom_buttons(frm);
      if(frm.doc.status == 'Approved' && !frm.doc.bom_created){
        create_bom_button(frm);   
      }

    },

    check_dr_required:  function(frm){
        let dr_required = 0;
        frm.doc.design_details.forEach(function(detail) {
            if(detail.dr_required == 1){
                dr_required = 1;
            }
        });
        frm.set_value('dr_required_check', dr_required)
    },
    validate: function(frm){
        frm.trigger('check_dr_required');
    }
});

let create_custom_buttons = function(frm){
  if(!frm.is_new() && frm.doc.status=='Draft'){
    frm.add_custom_button('Request For Verification',() =>{
      request_for_verification(frm);
    }, 'Actions');
  }
  approve_design_analysis(frm);
  request_for_approval(frm);
}

let create_bom_button = function(frm){
    if(!frm.is_new()){
      frm.add_custom_button('Create BOM',() =>{
        create_bom(frm);
      },'Actions' );
    }
  }

let request_for_verification = function(frm){
  if(frm.doc.dr_required_check){
    frappe.call({
      method: 'aumms.aumms.doctype.design_analysis.design_analysis.create_design_request',
      args: {
        design_analysis: frm.doc.name
      },
      callback: (r) => {
                frm.reload_doc()
             },
    })
  }
  else{
    frm.scroll_to_field('verified_item');
    if(frm.doc.verified_item.length<1){
      frappe.msgprint("Please fill the verified item table");
    }
  }
}

let request_for_approval = function(frm){
  if((frm.doc.status == "Request For Verification" ) || (frm.doc.dr_required_check == 0 && frm.doc.verified_item.length>0 && frm.doc.status != 'Request For Approval' && frm.doc.status != 'Approved')){
    frm.add_custom_button('Request For Approval', () =>{
      make_request_for_approval(frm);
    },'Actions');
  }
}

let make_request_for_approval = function (frm) {
    let d = new frappe.ui.Dialog({
        title: __('Request for Approval'),
        fields: [
            {
                fieldtype: 'Check',
                label: 'Self Assign',
                fieldname: 'self_assign',
                default: 0,
                onchange: function (e) {
                    d.toggle_enable('assign_to', !e.checked);
                    if (e.checked) {
                        d.set_value('assign_to', frappe.session.user);
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
                        query: 'aumms.aumms.doctype.design_analysis.design_analysis.supervisor_user_query',
                    };
                },
                depends_on: 'eval: !doc.self_assign'
            }
        ],
        primary_action_label: __('Submit'),
        primary_action(values) {
            let assign_to = '';
            if (values.self_assign) {
                assign_to = frappe.session.user;
            }
            else {
                assign_to = values.assign_to;
            }
            if (assign_to == null) {
                frappe.msgprint('Please select an option');
            } else {
                frappe.call({
                    method: 'aumms.aumms.doctype.design_analysis.design_analysis.assign_design_analysis',
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
        }
    });
    d.show();
}

// Check if the logged-in user is a supervisor
const isSupervisor = frappe.user_roles.includes('Supervisor');
let approve_design_analysis = function(frm) {
    if (frm.doc.status == "Request For Approval") {
        if (isSupervisor) {
            frm.add_custom_button('Approve', () => {
                const item_code = frm.doc.item_code;
                const item_group = frm.doc.item_group;
                const purity = frm.doc.purity;
                const customer_expected_weight = frm.doc.customer_expected_weight;

                frappe.call({
                    method: 'aumms.aumms.doctype.design_analysis.design_analysis.create_aumms_item_from_design_analysis',
                    args: {
                        item: item_code,
                        item_group: item_group,
                        purity: purity,
                        customer_expected_weight: customer_expected_weight,
                    },
                    callback: (r) => {
                        if (r.message) {
                            frm.set_value('aumms_item', r.message);
                            frm.set_value("status","Approved")
                            frm.save();
                            console.log('AuMMS Item Created:', r.message);

                            
                        } else {
                            console.log('Failed to create AuMMS Item');
                        }

                    }
                    
                });
            }, 'Actions');
              

            frm.add_custom_button('Reject', () =>{
              reject_design_analysis(frm)
            },'Actions');
        }
    }
}

let reject_design_analysis = function(frm){
  let d = new frappe.ui.Dialog({
    title: 'Reason for Rejection',
    fields: [
        {
            label: 'Comment',
            fieldname: 'comment',
            fieldtype: 'Small Text',
            reqd: 1
        },
    ],
    size: 'small',
    primary_action_label: 'Add comment',
    primary_action(values) {
      frappe.call({
            method: 'aumms.aumms.utils.rejection_action',
            args: {
              'doctype': frm.doc.doctype,
              'doc':frm.doc.name,
              'comment':values.comment
            },
            callback: function(r) {
              if (r.message){
                frm.set_value("status","Rejected")
                frm.save()
                frappe.show_alert({
                  message:__('Rejected........'),
                  indicator:'red'
                }, 5);
              }
            }
          })
        d.hide();
    }
});

d.show();
}
function create_bom(frm) {

    let bom_dia = new frappe.ui.Dialog({
        title: __('Request for BOM'),
        fields: [
            {
                fieldtype: 'Check',
                label: 'Self Assign',
                fieldname: 'self_assign',
                default: 0,
                onchange: function (e) {
                    d.toggle_enable('assign_to', !e.checked);
                    if (e.checked) {
                        d.set_value('assign_to', frappe.session.user);
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
                        query: 'aumms.aumms.doctype.design_analysis.design_analysis.head_of_smith_user_query',
                    };
                },
                depends_on: 'eval: !doc.self_assign'
            }
        ],
        primary_action_label: __('Submit'),
        primary_action(values) {
            let assign_to = '';
            if (values.self_assign) {
                assign_to = frappe.session.user;
            }
            else {
                assign_to = values.assign_to;
            }
            if (assign_to == null) {
                frappe.msgprint('Please select an option');
            } else {
                frappe.call({
                    method: 'aumms.aumms.doctype.design_analysis.design_analysis.create_bom_function',
                    args: {
                        doctype: frm.doctype,
                        docname: frm.doc.name,
                        assign_to: assign_to
                    },
                    freeze: true,
                    callback: (r) => {
                        frm.reload_doc();
                        bom_dia.hide();
                    }
                });
            }
        }
    });
    bom_dia.show()
}

frappe.ui.form.on('Verified Item',{
    item: function(frm,cdt,cdn){
        let d = locals[cdt][cdn];
        var gold_weight = 0
        var expected_weight = 0
        var calculated_stone_weight = 0
        frm.doc.verified_item.forEach(function(d){
            gold_weight += d.gold_wt;
            expected_weight += d.net_wt;
            calculated_stone_weight += d.stone_wt;
        })
        frm.set_value('gold_weight',gold_weight),
        frm.set_value('expected_weight',expected_weight),
        frm.set_value('calculated_stone_weight',calculated_stone_weight)
    },
    verified_item_remove: function(frm){
        var expected_weight = 0
        var gold_weight = 0
        var calculated_stone_weight = 0
        frm.doc.verified_item.forEach(function(d){
            gold_weight += d.gold_wt;
            expected_weight += d.net_wt;
            calculated_stone_weight += d.stone_wt;
        })
        frm.set_value('gold_weight',gold_weight),
        frm.set_value('expected_weight',expected_weight)
        frm.set_value('calculated_stone_weight',calculated_stone_weight)
    },
});
