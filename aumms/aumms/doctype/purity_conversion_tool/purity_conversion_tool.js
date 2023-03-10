// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Purity Conversion Tool', {
	refresh: function (frm) {
		frm.disable_save();
		clear_values(frm);
		// set filter for item_type
		set_filter('item_type', { is_purity_item: 1 });
		// set filter for uom
		set_filter('uom', { is_purity_uom: 1 });
		// set filter for uom_of_gold_in_hand
		set_filter('uom_of_gold_in_hand', { is_purity_uom: 1 });
		// set filter for uom_of_gold_to_be_obtained
		set_filter('uom_of_gold_to_be_obtained', { is_purity_uom: 1 });
		frm.set_value('party_type', '')

	},
	purity: function (frm) {
		if (frm.doc.purity && validate_mandatory_fields(frm)) {
			prepare_conversion_chart(frm);
		}
		else {
			clear_values(frm);
		}
	},
	party(frm) {
		if (frm.doc.party && frm.doc.purity && frm.doc.item_type) {
			frm.trigger('purity')
		} else {
			clear_values(frm);
		}
	},
	item_type(frm) {
		if (!frm.doc.item_type) {
			frm.set_value('purity', '')
		}
	},
	party_type(frm) {
		frm.set_value('party', '')
	},
	uom(frm) {
		if (frm.doc.uom) {
			show_total_gw_and_aw(frm);
		}
	},
	uom_of_gold_in_hand(frm) {
		if (frm.doc.uom_of_gold_in_hand) {
			if (!frm.doc.uom_of_gold_to_be_obtained) {
				frm.set_value('uom_of_gold_to_be_obtained', frm.doc.uom_of_gold_in_hand)
			}
		}
		frm.trigger('gold_in_hand')
	},
	uom_of_gold_to_be_obtained(frm) {
		frm.trigger('gold_in_hand')
	},
	purity_percentage_in_hand(frm) {
		if (0 > frm.doc.purity_percentage_in_hand || frm.doc.purity_percentage_in_hand  > 100) {
			frappe.throw(__('Purity Percentage must range from 0 to 100'));
		}
		frm.trigger('gold_in_hand')
	},
	purity_percentage_to_be_obtained(frm) {
		if (0 > frm.doc.purity_percentage_to_be_obtained || frm.doc.purity_percentage_to_be_obtained  > 100) {
			frappe.throw(__('Purity Percentage must range from 0 to 100'));
		}
		frm.trigger('gold_in_hand')
	},
	purity_in_hand(frm){
		if (frm.doc.purity_in_hand) {
			set_purity_percentage(frm.doc.purity_in_hand, 'purity_percentage_in_hand')
		}
	},
	purity_to_be_obtained(frm) {
		if (frm.doc.purity_to_be_obtained) {
			set_purity_percentage(frm.doc.purity_to_be_obtained, 'purity_percentage_to_be_obtained')
		}
	},
	gold_in_hand(frm) {
		if (frm.doc.gold_in_hand) {
			frm.call('get_gold_to_be_obtained')
				.then(r => {
					if (r.message) {
						frm.set_df_property('alloy_obtained', 'label', 'Alloy obtained From the Conversion in '+ frm.doc.uom_of_gold_to_be_obtained)
						frm.set_df_property('gold_obtained', 'label',
						'Gold obtained from '+frm.doc.gold_in_hand+' '
						+frm.doc.uom_of_gold_in_hand +' of '+frm.doc.purity_percentage_in_hand+'% purity '+
						' to '+frm.doc.purity_percentage_to_be_obtained+ '% purity in '+frm.doc.uom_of_gold_to_be_obtained)
						frm.set_value('gold_obtained', r.message.gold_weight)
						frm.set_value('alloy_obtained', r.message.alloy_weight)
					} else {
						clear_values(frm)
					}
				})
		} else {
			clear_values(frm)
		}
	}
});

function validate_mandatory_fields(frm) {
	var validated = 0;
	if (frm.doc.party && frm.doc.party_type) {
		validated = 1;
	}
	else {
		frappe.throw(__('Party Type and Part is required to do this action.'));
	}
	if (frm.doc.item_type) {
		validated = 1;
	}
	else {
		frappe.throw(__('Item Type is required to do this action.'));
	}
	return validated;
}

function prepare_conversion_chart(frm) {
	if (frm.doc.party_type && frm.doc.party && frm.doc.item_type && frm.doc.purity) {
		frappe.call({
			method: 'aumms.aumms.doctype.purity_conversion_tool.purity_conversion_tool.get_metal_ledger_entries',
			args: {
				party_type: frm.doc.party_type,
				party: frm.doc.party,
				item_type: frm.doc.item_type,
				purity: frm.doc.purity
			},
			freeze: true,
			freeze_message: __("Preparing Conversion Chart.."),
			callback: (r) => {
				if (r && r.message) {
					frm.clear_table('conversion_charts');
					r.message.forEach(conversion_chart => {
						let conversion_charts = frm.add_child('conversion_charts');
						conversion_charts.item_code = conversion_chart.item_code;
						conversion_charts.item_name = conversion_chart.item_name;
						conversion_charts.gold_in_hand_purity = conversion_chart.gold_in_hand_purity;
						conversion_charts.gold_in_hand_weight = conversion_chart.qty;
						conversion_charts.stock_uom = conversion_chart.stock_uom;
						conversion_charts.purity_to_be_obtained = conversion_chart.purity_to_be_obtained;
						conversion_charts.gold_weight_to_be_obtained_for_the_purity = conversion_chart.gold_weight;
						conversion_charts.alloy_weight = conversion_chart.alloy_weight;
						conversion_charts.voucher_type = conversion_chart.voucher_type;
					});
					frm.refresh_field('conversion_charts');
					frm.trigger('uom')
				}
			},
			error: (r) => {
				frappe.throw(__(r));
			}
		})
	}
}

let clear_values = function (frm) {
	// clear field values
	frm.set_value('total_gold_weight_to_be_obtained_for_the_purity', 0)
	frm.set_value('total_alloy_weight', 0)
	frm.clear_table('conversion_charts');
	frm.refresh_field('conversion_charts');
	frm.set_value('alloy_obtained', '')
	frm.set_value('gold_obtained', '')
}
let set_filter = function (field, filters) {
	/*
		function to set filter for a specific field
		args:
			field: field name
			filters: set of filters, (eg: {key:value})
		output: filter applied list for field
	*/
	cur_frm.set_query(field, () => {
		return {
			filters: filters
		}
	})
}

let show_total_gw_and_aw = function (frm) {
	// call to get total gold weight and alloy weight
	frm.call('add_gw_and_aw')
		.then(r => {
			if (r.message) {
				// set total GW and AW
				let gw = 'total_gold_weight_to_be_obtained_for_the_purity'
				frm.set_value(gw, r.message.gw)
				frm.set_value('total_alloy_weight', r.message.aw)
				// set label for total GW and AW
				frm.set_df_property(gw, 'label', 'Total Gold Weight to be obtained for the purity ' + frm.doc.purity + ' In ' + frm.doc.uom);
				frm.set_df_property('total_alloy_weight', 'label', 'Total Alloy Weight to be obtained for the purity ' + frm.doc.purity + ' In ' + frm.doc.uom);
			}
		})
}

let set_purity_percentage = function(purity, field) {
	frappe.call({
		method: 'aumms.aumms.doctype.purity_conversion_tool.purity_conversion_tool.get_purity_percentage',
		args: {
			purity: purity
		},
		callback: (r) => {
			if (r.message) {
				cur_frm.set_value(field, r.message)
			}
		}
	})
}