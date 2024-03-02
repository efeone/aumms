// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('AuMMS Item', {
  setup(frm) {
    set_filters(frm);
  },
  onload(frm) {
    frm.trigger('is_purity_item');
  },
  is_purity_item(frm) {
    if (frm.doc.is_purity_item) {
      set_filter('stock_uom', { is_purity_uom: 1, enabled: 1 });
      set_filter('purchase_uom', { is_purity_uom: 1, enabled: 1 });
      set_filter('sales_uom', { is_purity_uom: 1, enabled: 1 });
      set_filter('weight_uom', { is_purity_uom: 1, enabled: 1 });
    } else {
      set_filter('stock_uom', { enabled: 1 });
      set_filter('purchase_uom', { enabled: 1 });
      set_filter('sales_uom', { enabled: 1 });
      set_filter('weight_uom', { enabled: 1 });
    }
  },
  stock_uom(frm) {
    if (frm.doc.stock_uom && frm.doc.is_purity_item) {
      append_purity_uoms(frm);
    }
  },
  item_group(frm) {
    frm.set_value('stock_uom', );
    frappe.call({
      // set making_charge_percentage, is_purchase_item and is_sales_item from item group
      method: 'aumms.aumms.doc_events.item.making_charge_to_item',
      args: {
        'item_group': frm.doc.item_group,
        'charge_based_on': frm.doc.making_charge_based_on,
        'type': frm.doc.item_type
      },
      callback: function (r) {
        if (r.message) {
          frm.set_value('making_charge_percentage', r.message['making_charge_percentage']);
          frm.set_value('is_purchase_item', r.message['is_purchase_item']);
          frm.set_value('is_sales_item', r.message['is_sales_item']);
          frm.refresh_field('making_charge_percentage');
        }
        else {
          frm.set_value('making_charge_percentage', 0);
        }
      }
    })
    if (frm.doc.making_charge_based_on) {
      frappe.call({
        // set making_charge_percentage and making_charge while change of making_charge_based_on
        method: 'aumms.aumms.doc_events.item.fetch_making_charge_from_item_group_to_item',
        args: {
          'item_group': frm.doc.item_group,
          'charge_based_on': frm.doc.making_charge_based_on,
          'type': frm.doc.item_type
        },
        callback: function (r) {
          if (r.message) {
            frm.set_value('making_charge_percentage', r.message['percentage']);
            frm.set_value('making_charge', r.message['currency']);
          }
          else {
            frm.set_value('making_charge_percentage', 0);
            frm.set_value('making_charge', 0);
          }
        }
      })
    }
  },
  calculate_weight_per_unit(frm){
    frm.set_value('weight_per_unit', frm.doc.gold_weight + frm.doc.stone_weight);
  },
  gold_weight(frm){
    frm.trigger('calculate_weight_per_unit');
  },
  stone_weight(frm){
    frm.trigger('calculate_weight_per_unit');
  },
  has_stone(frm){
    if(!frm.doc.has_stone){
      frm.clear_table('stone_details');
      frm.set_value('stone_weight', 0);
      frm.set_value('stone_charge', 0);
    }
    frm.toggle_display('is_stone_item', !frm.doc.has_stone);
  },
  is_stone_item(frm) {
    frm.toggle_display('has_stone', !frm.doc.is_stone_item);
  },
  triger_checkbox_display(frm){
    if(frm.doc.is_stone_item || frm.doc.has_stone){
      frm.toggle_display('has_stone', !frm.doc.is_stone_item);
      frm.toggle_display('is_stone_item', !frm.doc.has_stone);
    }
  },
  refresh(frm){
    frm.trigger('triger_checkbox_display');
    if (!frm.is_new()){
      frm.disable_form();
    }
  }
});

frappe.ui.form.on("UOM Conversion Detail", {
	uom: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if (row.uom) {
			frappe.call({
				method: "erpnext.stock.doctype.item.item.get_uom_conv_factor",
				args: {
					"uom": row.uom,
					"stock_uom": frm.doc.stock_uom
				},
				callback: function(r) {
					if (!r.exc && r.message) {
						frappe.model.set_value(cdt, cdn, "conversion_factor", r.message);
					}
				}
			});
		}
	}
});

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

let append_purity_uoms = function (frm) {
  /*
      function to append uoms table with all purity uoms
      args:
          frm: current document
  */
  // clear uom table
  frm.clear_table('uoms');
  frm.refresh_field('uoms');

  let uoms = [];
  let existing_uom = [];

  // add first uom
  frm.add_child('uoms', {
    'uom': frm.doc.stock_uom,
    'conversion_factor': 1
  })
  uoms.push(frm.doc.stock_uom);
  frm.refresh_field('uoms');
  // update existing_uom
  existing_uom = get_existing_uoms(uoms);
  // call to get list of purity uoms
  frappe.call('aumms.aumms.doc_events.item.get_purity_uom')
    .then(r => {
      r.message.forEach(uom => {
        // check uom not in exising uom list and add uom
        if (!existing_uom.includes(uom.name)) {
          let uoms = frm.add_child('uoms');
          uoms.uom = uom.name;
        }
      });
      frm.refresh_field('uoms');
      //trigger all uom of uoms
      trigger_uoms();
    })
}

let get_existing_uoms = function (uoms) {
  // function to get all existing uom in the doc as list
  if (cur_frm.doc.uoms) {
    cur_frm.doc.uoms.forEach(uom => {
      uoms.push(uom.uom);
    });
  }
  return uoms;
}

let trigger_uoms = function () {
  // function to trigger every uom of uoms table
  if (cur_frm.doc.uoms) {
    cur_frm.doc.uoms.forEach(uom => {
      // trigger uom field
      cur_frm.script_manager.trigger('uom', uom.doctype, uom.name);
    });
  }
  cur_frm.refresh_field('uoms');
}

let set_filters = function(frm){
  frm.set_query('item_name', 'stone_details', () => {
    return {
      filters: {
        is_stone_item: 1,
      }
    }
  });
}

frappe.ui.form.on("Stone Details", {
  stone_weight: function(frm, cdt, cdn) {
    calculate_stone_weight_and_charge(frm);
  },
  stone_charge: function(frm, cdt, cdn) {
    calculate_stone_weight_and_charge(frm);
  },
  stone_details_add: function(frm, cdt, cdn) {
    calculate_stone_weight_and_charge(frm);
  },
  stone_details_remove: function(frm, cdt, cdn) {
    calculate_stone_weight_and_charge(frm);
  }
});

let calculate_stone_weight_and_charge = function(frm){
  let stone_weight = 0;
  let stone_charge = 0;
  frm.doc.stone_details.forEach(stone_detail => {
    if(stone_detail.stone_weight){
      stone_weight += stone_detail.stone_weight
    }
    if(stone_detail.stone_charge){
      stone_charge += stone_detail.stone_charge
    }
  });
  frm.set_value('stone_weight', stone_weight);
  frm.set_value('stone_charge', stone_charge);
}
