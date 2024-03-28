// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on("Manufacturing Request", {
  refresh: function(frm) {
		frm.set_query('uom',()=>{
			return {
				filters: {
					"is_purity_uom": 1
				}
			}
		});
  }
});

frappe.ui.form.on("Manufacturing Request Stage", {
  select_raw_material: function(frm, cdt , cdn) {
    let row = locals[cdt][cdn]
    frappe.new_doc('Raw Material Bundle', {
      'manufacturing_request': frm.doc.name,
      'manufacturing_stage' : row.manufacturing_stage,
    })
  },
  create_job_card: function(frm, cdt, cdn) {
    frm.call('create_jewellery_job_card', { 'stage_row_id': cdn }).then(r => {
        frm.refresh_fields();
    });
  },
  awaiting_raw_material: function(frm, cdt, cdn) {
    let row = locals[cdt][cdn]
    if (row.awaiting_raw_material) {
      frm.call('update_previous_stage', {idx:row.idx}).then(r=>{
        row.previous_stage = r.message
        frm.refresh_fields()
      })
    }
  },
  completed: function(frm, cdt, cdn) {
        let allcompleted = true;
        let childTable = frm.doc.manufacturing_request_stage;
        for (let i = 0; i < childTable.length; i++) {
            if (!childTable[i].completed) {
                allcompleted = false;
                break;
            }
        }
        frm.set_value('status', allcompleted ? 'Completed' : 'Open');
    }
});
