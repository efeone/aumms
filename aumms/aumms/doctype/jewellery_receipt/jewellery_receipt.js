frappe.ui.form.on("Jewellery Receipt", {
  setup: function (frm) {
      frm.set_query('uom', 'item_details', () => {
          return {
              filters: {
                  "is_purity_uom": 1
              }
          }
      });
  },
  refresh:function(frm) {
    frm.set_query('stone', 'item_details', () => {
      return {
        filters: {
          "is_stone_item": 1
        }
      }
    })
  },
  item_category: function(frm) {
    frm.events.update_item_details_table(frm);
  },
  item_type: function(frm) {
    frm.events.update_item_details_table(frm);
  },
  item_group:function(frm) {
    frm.events.update_item_details_table(frm);
  },
  purity: function(frm) {
    frm.events.update_item_details_table(frm);
  },
  board_rate: function(frm) {
    frm.events.update_item_details_table(frm);
  },
  update_item_details_table: function(frm){
    if(frm.doc.item_details){
      frm.doc.item_details.forEach(function(item){
        frappe.model.set_value(item.doctype, item.name, 'item_category', frm.doc.item_category);
        frappe.model.set_value(item.doctype, item.name, 'item_type', frm.doc.item_type);
        frappe.model.set_value(item.doctype, item.name, 'item_group', frm.doc.item_group);
        frappe.model.set_value(item.doctype, item.name, 'purity', frm.doc.purity);
        frappe.model.set_value(item.doctype, item.name, 'board_rate', frm.doc.board_rate);

      });
    }
    frm.refresh_fields();
  },

  // has_stone: function (frm) {
  //   if(!frm.doc.has_stone){
  //     frm.set_value('stone', );
  //   }
  //   frm.fields_dict.item_details.grid.toggle_enable('has_stone', frm.doc.has_stone);
  //   frm.refresh_fields();
  //   frm.trigger('update_item_details');
  // },
  // stone: function(frm){
  //   frm.trigger('update_item_details');
  // },
  // update_item_details: function(frm){
  //   if(frm.doc.item_details){
  //     frm.doc.item_details.forEach(function(item){
  //       frappe.model.set_value(item.doctype, item.name, 'has_stone', frm.doc.has_stone);
  //       frappe.model.set_value(item.doctype, item.name, 'stone', frm.doc.stone);
  //     });
  //   }
  //   frm.refresh_fields();
  // },
  // create_item: function(frm) {
  //   if (frm.is_new()) {
  //      create_item_details(frm);
  //      frm.trigger('update_item_details_table');
  //   }
  // },
  quantity: function(frm) {
        var quantity = frm.doc.quantity;
        var cur_items_len = frm.doc.item_details.length;

        if (quantity < cur_items_len) {
            frm.doc.item_details.splice(quantity);
        } else {
            for (var i = cur_items_len; i < quantity; i++) {
                let row = frm.add_child('item_details', {
                    item_category: frm.doc.item_category,
                    item_type: frm.doc.item_type,
                    item_group: frm.doc.item_group,
                    purity: frm.doc.purity,
                    board_rate: frm.doc.board_rate
                });
            }
        }

        frm.refresh_field('item_details');
    }
});
frappe.ui.form.on("Jewellery Item Receipt", {
    form_render	: function(frm, cdt, cdn) {
        let d = locals[cdt][cdn];
        if (d.has_stone) {
            let net_weight = d.gold_weight + d.stone_weight;
            frappe.model.set_value(cdt, cdn, 'net_weight', net_weight);
        }
    },
    stone_weight: function(frm, cdt, cdn){
      let d = locals[cdt][cdn];
      if (d.single_stone){
        let net_weight = d.gold_weight + d.stone_weight;
        frappe.model.set_value(cdt, cdn, 'net_weight', net_weight);
        let stone_charge = d.unit_stone_charge * d.stone_weight;
        frappe.model.set_value(cdt, cdn, 'stone_charge', stone_charge);
      }
    },
    making_charge : function(frm, cdt, cdn){
      if (d.making_charge) {
        let amount = d.amount_without_making_charge + d.making_charge
        frappe.model.set_value(cdt, cdn, 'amount', amount);
      }frm.fields_dict.item_details.grid.toggle_enable('has_stone', frm.doc.has_stone);frm.fields_dict.item_details.grid.toggle_enable('has_stone', frm.doc.has_stone);
    },
    gold_weight: function(frm, cdt, cdn) {
      let d = locals[cdt][cdn];
      if (! d.has_stone) {
          let net_weight = d.gold_weight;
          frappe.model.set_value(cdt, cdn, 'net_weight', net_weight);
          let amount_without_making_charge = (d.gold_weight * frm.doc.board_rate)
          frappe.model.set_value(cdt, cdn, 'amount_without_making_charge', amount_without_making_charge);
        }
    },
    making_chargein_percentage: function(frm, cdt, cdn) {
      let d = locals[cdt][cdn];
      if (d.amount_without_making_charge && d.making_chargein_percentage) {
          let making_charge = d.amount_without_making_charge * (d.making_chargein_percentage / 100);
          frappe.model.set_value(cdt, cdn, 'making_charge', making_charge);
      }
    },
    making_charge: function(frm, cdt, cdn) {
        let d = locals[cdt][cdn];
        if (d.making_charge) {
            let amount = d.amount_without_making_charge + d.making_charge
            frappe.model.set_value(cdt, cdn, 'amount', amount);
        }
    },
    stone_charge : function(frm, cdt, cdn){
      let d = locals[cdt][cdn];
      if (d.has_stone){
        let amount_without_making_charge = (d.gold_weight * frm.doc.board_rate) + d.stone_charge
        frappe.model.set_value(cdt, cdn, 'amount_without_making_charge', amount_without_making_charge);
      }
    },
    add_multi_stone: function(frm, cdt, cdn) {
      if (frm.is_new()) {
         create_multi_stone(frm, cdt, cdn);
      }
    }
});

let create_multi_stone = function(frm, cdt, cdn) {
  let d = new frappe.ui.Dialog({
    title: 'Enter Stone Details',
    fields: [
      {
        label: 'UOM',
        fieldname: 'uom',
        fieldtype: 'Link',
        options: 'UOM',
        reqd: 1
      },
      {
        label: 'Gold Weight',
        fieldname: 'gold_weight',
        fieldtype: 'Float',
        reqd: 1,
      },
      {
        label: 'Making Charge In Percentage',
        fieldname: 'making_charge_in_percentage',
        fieldtype: 'Percent',
        reqd: 1
      },
      {
        label: 'Stone Details',
        fieldname: 'stone_details',
        fieldtype: 'Table',
        reqd: 1,
        annotatable: true,
        editable: true,
        fields: [
          {
            label: 'Stone',
            fieldname: 'stone',
            fieldtype: 'Link',
            in_list_view: 1,
            options: 'AuMMS Item'
          },
          {
            label: 'Stone Weight',
            fieldname: 'stone_weight',
            fieldtype: 'Float',
            in_list_view: 1
          }
        ]
      },
      {
        label: 'Total Stone Weight',
        fieldname: 'total_stone_weight',
        fieldtype: 'Float',
      },
      {
        label: 'Unit of Stone Charge',
        fieldname: 'unit_stone_charge',
        fieldtype: 'Int',
        reqd: 1
      },
    ],
    primary_action_label: 'Submit',
    primary_action: function(values) {
      var quantity = frm.doc.quantity;
      for (var i = 0; i < quantity; i++) {
        var child = locals[cdt][cdn]
        if (!child) {
          // If the child at index 'i' doesn't exist, add a new row
          child = frm.add_child('item_details', {
            item_category: frm.doc.item_category,
            item_type: frm.doc.item_type,
            item_group: frm.doc.item_group,
            purity: frm.doc.purity,
            board_rate: frm.doc.board_rate
          });
        }
        // Update the corresponding fields for the current child row
        child.uom = values.uom;
        child.gold_weight = values.gold_weight;
        child.making_chargein_percentage = values.making_charge_in_percentage;
        child.stone_charge = 0;
        let stone_weight = "";
        let stone_names = "";

        for (let j = 0; j < values.stone_details.length; j++) {
          let stone = values.stone_details[j];
          stone_names += stone.stone;
          stone_weight += stone.stone_weight;

          if (j < values.stone_details.length - 1) {
            stone_names += ", ";
            stone_weight += ", ";
          }
        }
        child.stones = stone_names;
        child.individual_stone_weight = stone_weight;
        child.stone_weight = values.total_stone_weight;
        child.unit_stone_charge = values.unit_stone_charge;
        child.has_stone = 1;

        let stone_charge = values.unit_stone_charge * values.total_stone_weight;
        child.stone_charge = stone_charge;

        let amount_without_making_charge = (values.gold_weight * frm.doc.board_rate) + stone_charge;
        child.amount_without_making_charge = amount_without_making_charge;

        let making_charge = amount_without_making_charge * (values.making_charge_in_percentage / 100);
        child.making_charge = making_charge;

        let amount = amount_without_making_charge + making_charge;
        child.amount  = amount;

      }

      refresh_field('item_details');
      d.hide();
    }
  });

  function calculate_total_stone_weight() {
    let total_weight = 0;
    let stone_details = d.get_value('stone_details');
    if (stone_details && stone_details.length > 0) {
      stone_details.forEach(function(row) {
        total_weight += row.stone_weight || 0;
      });
    }
    d.set_value('total_stone_weight', total_weight);
  }

  document.addEventListener('change', function(event) {
    if (event.target.matches('[data-fieldname="stone_weight"]')) {
      calculate_total_stone_weight();
    }
  });

  if ('stone_details' in d.fields_dict) {
    d.fields_dict.stone_details.grid.get_field('stone').get_query = function() {
        return {
            filters: {
                "is_stone_item": 1
            }
        };
    };
  };
  if ('uom' in d.fields_dict) {
    d.fields_dict.uom.get_query = function() {
      return {
        filters: {
          "is_purity_uom": 1
        }
      }
    }
  }
  d.show();
};
