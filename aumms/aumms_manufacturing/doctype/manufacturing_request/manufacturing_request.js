// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on("Manufacturing Request", {
	setup: function(frm) {
		set_filters(frm);
		marked_as_previous_stage_completed(frm)
		make_connections_read_only(frm);
	},
	onload: function(frm) {
		hide_add_row_button(frm);
	},
	refresh: function(frm) {
		if(!frm.is_new){
			hide_add_row_button(frm);
		}
		marked_as_previous_stage_completed(frm)
		if(!frm.doc.product)
		{
			frm.toggle_display("product",false);
		}
		if(!frm.doc.weight && frm.doc.weight <= 0)
		{
			frm.toggle_display("weight",false);
		}
		add_smith_buttons(frm);
	},
});

/* Everything here needs a submitted request and the smith who finished the piece, so the
   buttons only stand once the last stage has one. */
function add_smith_buttons(frm) {
	if (frm.doc.docstatus !== 1) {
		return;
	}
	let last_stage = (frm.doc.manufacturing_stages || []).slice(-1)[0];
	if (!last_stage || !last_stage.smith) {
		return;
	}

	if (!frm.doc.buy_back_stock_entry) {
		frm.add_custom_button(__('Buy Back Finished Goods'), () => {
			frappe.confirm(
				__('Move {0} from {1} back to {2}?', [
					frm.doc.product, last_stage.smith_warehouse, frm.doc.supervisor_warehouse
				]),
				() => {
					frm.call('buy_back_finished_good').then(() => frm.reload_doc());
				}
			);
		}, __('Create'));
	}

	frm.add_custom_button(__('Settle Smith Payment'), () => {
		frappe.new_doc('Smith Settlement', {
			'smith': last_stage.smith,
			'manufacturing_request': frm.doc.name,
			'company': frm.doc.company
		});
	}, __('Create'));

	frm.add_custom_button(__("Smith's Metal Ledger"), () => {
		frappe.set_route('query-report', 'Metal Ledger', {
			'party_type': 'Smith',
			'party': last_stage.smith,
			'from_date': frappe.datetime.add_months(frm.doc.creation, -1),
			'to_date': frappe.datetime.get_today()
		});
	}, __('View'));

	/* The request writes two stock entries that read alike on a list, so each is named
	   for the leg it moves rather than both being offered as "Stock Entry". */
	if (frm.doc.manufacture_stock_entry) {
		frm.add_custom_button(__('Manufacture Entry'), () => {
			frappe.set_route('Form', 'Stock Entry', frm.doc.manufacture_stock_entry);
		}, __('View'));
	}
	if (frm.doc.buy_back_stock_entry) {
		frm.add_custom_button(__('Finished Goods Transfer'), () => {
			frappe.set_route('Form', 'Stock Entry', frm.doc.buy_back_stock_entry);
		}, __('View'));
	}
}

/* Connections are there to reach the documents a request already has, not to raise new ones.
   A bundle is raised from its stage row and a job card from its own button, both of which
   carry the stage the document belongs to, which the plus on a connection cannot. */
function make_connections_read_only(frm) {
	frm.can_make_methods = Object.fromEntries(
		(frm.meta.links || []).map(link => [link.link_doctype, () => false])
	);
}

function set_filters(frm) {
	frm.set_query('uom', function() {
		return {
			filters: {
				is_purity_uom : 1
			}
		};
	});
}

function marked_as_previous_stage_completed(frm) {
	if (frm.doc.manufacturing_stages && frm.doc.manufacturing_stages.length > 0) {
		frm.doc.manufacturing_stages[0].previous_stage_completed = 1;
		frm.doc.manufacturing_stages[0].is_first_stage = 1;
		const last_index = frm.doc.manufacturing_stages.length - 1;
		frm.doc.manufacturing_stages[last_index].is_last_stage = 1;
		refresh_field('manufacturing_stages');
	}
}

function hide_add_row_button(frm) {
		if (frm.doc.manufacturing_stages && frm.fields_dict.manufacturing_stages.grid) {
				setTimeout(() => {
						frm.fields_dict.manufacturing_stages.grid.wrapper.find('.grid-add-row').hide();
						frm.fields_dict.manufacturing_stages.grid.wrapper.find('.grid-add-multiple-rows').hide();
				}, 1000);
		}
}


frappe.ui.form.on("Manufacturing Request Stage", {
	create_raw_material_bundle: function(frm, cdt , cdn) {
		let row = locals[cdt][cdn];
		frappe.new_doc('Raw Material Bundle', {
			'manufacturing_request': frm.doc.name,
			'stage' : row.manufacturing_stage,
			'manufacturing_stage' : row.name,
			'source_warehouse' : frm.doc.supervisor_warehouse,
			'expected_execution_time' : row.required_time
		})
	},
	create_job_card: function(frm, cdt, cdn) {
		frm.call('create_jewellery_job_card', { 'stage_row_id': cdn }).then(r => {
			frm.refresh_fields();
		});
	},
	previous_stage_completed: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn]
		if (row.previous_stage_completed) {
			update_previous_stage(frm, row.idx).then(previousStage => {
				row.previous_stage = previousStage;
				frm.refresh_field('manufacturing_stages');
			});

			update_previous_stage_weight(frm, row.idx).then(previousStageWeight => {
				row.previous_stage_weight = previousStageWeight;
				frm.refresh_field('manufacturing_stages');
			});
		}
	},
	raw_material_available: function(frm, cdt, cdn) {
		let d = frm.doc.manufacturing_stages;
		let current_index = -1;
		for (let i = 0; i < d.length; i++) {
			if (d[i].name === cdn) {
				current_index = i;
				break;
			}
		}
		if (frm.doc.manufacturing_stages[current_index].raw_material_available) {
			if (current_index < d.length - 1) {
				let next_row = d[current_index + 1];
				next_row.allow_to_start_only_if_raw_material_available = 1;
				frm.refresh_field('manufacturing_stages');
			}
		}
	},
});

function update_previous_stage(frm, idx) {
	return frm.call('update_previous_stage', { idx: idx }).then(r => {
		return r.message;
	});
}

function update_previous_stage_weight(frm, idx) {
	return frm.call('update_previous_stage_weight', { idx: idx }).then(r => {
		return r.message;
	});
}
