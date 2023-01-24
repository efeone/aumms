// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Purity Conversion Tool', {
	refresh: function(frm) {
		frm.disable_save();
    set_filters(frm);
	},
	purity: function(frm){
		if(validate_mandatory_fields(frm) && frm.doc.purity){
			prepare_conversion_chart(frm);
		}
		else{
			frm.clear_table('conversion_charts');
			frm.refresh_field('conversion_charts');
		}
	}
});

function set_filters(frm){
  frm.set_query('item_type', function() {
    return {
      filters: {
        purity_mandatory : 1
      }
    };
  });
}

function validate_mandatory_fields(frm){
	var validated = 0;
	if(frm.doc.party && frm.doc.party_type){
		validated = 1;
	}
	else {
		frappe.throw(__('Party Type and Part is required to do this action.'));
	}
	if(frm.doc.item_type){
		validated = 1;
	}
	else {
		frappe.throw(__('Item Type is required to do this action.'));
	}
	return validated;
}

function prepare_conversion_chart(frm){
	if(frm.doc.party_type && frm.doc.party && frm.doc.item_type && frm.doc.purity){
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
				if(r && r.message){
					frm.clear_table('conversion_charts');
					r.message.forEach(conversion_chart => {
						console.log(conversion_chart);
						let conversion_charts = frm.add_child('conversion_charts');
						conversion_charts.item_code = conversion_chart.item_code;
						conversion_charts.item_name = conversion_chart.item_name;
						conversion_charts.gold_in_hand_purity = conversion_chart.gold_in_hand_purity;
						conversion_charts.gold_in_hand_weight = conversion_chart.qty;
						conversion_charts.stock_uom = conversion_chart.stock_uom;
						conversion_charts.purity_to_be_obtained = conversion_chart.purity_to_be_obtained;
						conversion_charts.gold_weight_to_be_obtained_for_the_purity = conversion_chart.gold_weight;
						conversion_charts.alloy_weight = conversion_chart.alloy_weight;
					});
					frm.refresh_field('conversion_charts');
				}
			},
			error: (r) => {
				frappe.throw(__(r));
			}
		})
	}
}
