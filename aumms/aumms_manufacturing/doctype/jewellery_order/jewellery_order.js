// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on("Jewellery Order", {
  refresh: function(frm) {
    frm.set_query('uom', () => {
      return {
        filters: {
          "is_purity_uom": 1
        }
      };
    });
    frm.set_query("item", "jewellery_order_items", () => {
      return {
        filters: {
          "item_type": frm.doc.type,
          "item_category": frm.doc.category
        }
      }
    });
    /* The totals are worked out on validate, so refresh only shows what is stored.
       Writing them here would dirty the form on every reload. */
    toggle_available_item_fields(frm);
    update_intro(frm);
		limit_item_details(frm)
  },
  quantity: function(frm) {
    limit_item_details(frm)
  },
  total_weight: function(frm) {
		update_intro(frm)
  },

});


frappe.ui.form.on("Jewellery Order Item", {
  weight: function(frm, cdt, cdn) {
    calculate_weight(frm);
  },

  jewellery_order_items_remove: function(frm) {
    calculate_weight(frm);
    update_available_item_quantity(frm);
		check_finished(frm);
  },

  jewellery_order_items_add: function(frm) {
    limit_item_details(frm);
    update_available_item_quantity(frm);
		check_finished(frm);
  },

  is_available: function(frm, cdt, cdn) {
    let all_finished = true;
    let total_weightage = 0;
    let childtable = frm.doc.jewellery_order_items || [];
    for (let i = 0; i < childtable.length; i++) {
      if (childtable[i].is_available) {
        total_weightage += childtable[i].weight || 0;
      }
      if (!childtable[i].is_available) {
        all_finished = false;
      }
    }
    frm.set_value('finished', all_finished ? 1 : 0);
		frm.set_value('weight_of_available_item', total_weightage);
    update_available_item_quantity(frm);
  },
  item: function(frm, cdt, cdn) {
    var d = locals[cdt][cdn];
    duplicate_item(frm, cdt, cdn);

  }
});

function update_intro(frm) {
  if (frm.doc.total_weight !== frm.doc.expected_total_weight) {
    if (!frm.doc.intro_set) {
      frm.set_intro('Expected Total weight must be equal to the sum of weight in Jewellery Order items', 'blue');
      frm.doc.intro_set = true;
    }
  } else {
    if (frm.doc.intro_set) {
      frm.set_intro('');
      frm.doc.intro_set = false;
    }
  }
}

function update_available_item_quantity(frm) {
	let total_qty = 0;
	if(frm.doc.jewellery_order_items){
		total_qty = frm.doc.jewellery_order_items.filter(function(row) {
			return row.is_available == 1;
		}).length;
	}
    frm.set_value('available_item_quantity', total_qty);
    toggle_available_item_fields(frm);
}

//Neither total is worth a slot on the form until an item is actually in stock
function toggle_available_item_fields(frm) {
    frm.toggle_display("weight_of_available_item", !!frm.doc.weight_of_available_item);
    frm.toggle_display("available_item_quantity", !!frm.doc.available_item_quantity);
}

function limit_item_details(frm) {
  if(frm.doc.quantity) {
      availa_quantity = frm.doc.quantity;
  }
  limit = availa_quantity;
  if (frm.doc.jewellery_order_items.length >= limit) {
      $(".btn.btn-xs.btn-secondary.grid-add-row").hide();
  } else {
      $(".btn.btn-xs.btn-secondary.grid-add-row").show();
  }
}

function duplicate_item(frm, cdt, cdn) {
	var list = frm.doc.jewellery_order_items.map(row => row.item)
	cur_frm.fields_dict.jewellery_order_items.grid.get_field("item").get_query = function(doc,cdt,cdn) {
		var child = locals[cdt][cdn]
			return {
			filters : [
				["AuMMS Item", "name", "not in", list],
				["AuMMS Item", "item_type", "=", frm.doc.type],
				["AuMMS Item", "item_category", "=", frm.doc.category],
			]
		}
	}
}

function check_finished(frm) {
  let all_available = true;
  let childtable = frm.doc.jewellery_order_items;
  for (let i = 0; i < childtable.length; i++) {
    if (!childtable[i].is_available) {
      all_available = false;
      break;
    }
  }
  frm.set_value('finished', all_available ? 1 : 0);
}

function calculate_weight(frm, cdt,cdn) {
  let weight_of_available_item = 0;
  let total_weight = 0;
  if(frm.doc.jewellery_order_items){
    frm.doc.jewellery_order_items.forEach(function(d) {
      if (d.is_available) {
          weight_of_available_item += d.weight || 0;
      }
      total_weight += d.weight || 0;
    });
  }
  frm.set_value('weight_of_available_item', weight_of_available_item);
  frm.set_value('total_weight', total_weight);
}
