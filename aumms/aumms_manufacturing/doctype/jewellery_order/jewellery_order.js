// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on("Jewellery Order", {
	refresh: function(frm) {
		let total_qty = frm.doc.jewellery_order_items.filter(function(row) {
			return row.is_available == 1;
		}).length;
		frm.set_value('available_item_quantity', total_qty);
		frm.set_query('uom', () => {
			return {
				filters: {
					"is_purity_uom": 1
				}
			};
		});
		frm.set_query("item", "jewellery_order_items", ()=> {
			return {
				filters: {
					"item_type": frm.doc.type,
					"item_category": frm.doc.category
				}
			}
		});
  	},
		quantity: function(frm) {
			limit_item_details(frm)
		}
});

frappe.ui.form.on("Jewellery Order Item",{
  weight: function(frm, cdt, cdn){
   let d = locals[cdt][cdn];
   var total_weightage = 0
   frm.doc.jewellery_order_items.forEach(function(d){
		 if (d.is_available) {
          total_weightage += d.weight;
    	}
   });
   frm.set_value('weight_of_available_item',total_weightage);
 },
 jewellery_order_items_remove:function(frm){
	 	let d = locals[cdt][cdn];
     var total_weightage = 0
     frm.doc.jewellery_order_items.forEach(function(d){
	       total_weightage += d.weight;
     })
     frm.set_value("weight_of_available_item",total_weightage);
   },
   jewellery_order_items_add: function(frm)  {
    limit_item_details(frm)
	},
	is_available: function(frm, cdt, cdn) {
        let all_finished = true;
        let childtable = frm.doc.jewellery_order_items;
        for (let i = 0; i < childtable.length; i++) {
            if (!childtable[i].is_available) {
                all_finished = false;
                break;
            }
        }
        frm.set_value('finished', all_finished ? 1 : 0);
    }
});

function limit_item_details(frm) {
	if(frm.doc.quantity){
		availa_quantity = frm.doc.quantity
	}
	limit = availa_quantity
  if (frm.doc.jewellery_order_items.length >= limit)  {
    $(".btn.btn-xs.btn-secondary.grid-add-row").hide();
  }
  else  {
    $(".btn.btn-xs.btn-secondary.grid-add-row").show();
  }
}
