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
    frm.set_query('stone', () => {
      return {
        filters: {
          is_stone_item: 1
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
  has_stone: function (frm) {
    if(!frm.doc.has_stone){
      frm.set_value('stone', );
    }
    frm.fields_dict.item_details.grid.toggle_enable('has_stone', frm.doc.has_stone);
    frm.refresh_fields();
    frm.trigger('update_item_details');
  },
  stone: function(frm){
    frm.trigger('update_item_details');
  },
  update_item_details: function(frm){
    if(frm.doc.item_details){
      frm.doc.item_details.forEach(function(item){
        frappe.model.set_value(item.doctype, item.name, 'has_stone', frm.doc.has_stone);
        frappe.model.set_value(item.doctype, item.name, 'stone', frm.doc.stone);
      });
    }
    frm.refresh_fields();
  },
  create_item: function(frm) {
    if (frm.is_new()) {
       create_item_details(frm);
       frm.trigger('update_item_details_table');
    }
  },
  quantity: function(frm) {
    var quantity = frm.doc.quantity;
    // Clear existing rows
    frm.clear_table("item_details");
    // Add new rows based on quantity
    for (var i = 0; i < quantity; i++) {
        var row = frappe.model.add_child(frm.doc, "Jewellery Receipt Item", "item_details");
    }
    // Refresh the grid
    frm.fields_dict["item_details"].grid.refresh();
    frm.trigger('update_item_details_table');
    // Refresh other fields if needed
    frm.refresh_fields();
  }
});

let create_item_details = function(frm) {
  let d = new frappe.ui.Dialog({
    title: 'Enter Item Details',
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
        default: 3000
      },
    ],
    primary_action_label: 'Submit',
    primary_action: function(values) {
      console.log(values);
      let stone_names = "";
      let stone_charge = 0;
      let stone_weight = "";
      for (let i = 0; i < values.stone_details.length; i++) {
          stone_names += values.stone_details[i].stone;
          stone_weight += values.stone_details[i].stone_weight;

          if (i < values.stone_details.length - 1) {
              stone_names += " , ";
              stone_weight += " , ";
          };
      }
      var child = frm.add_child('item_details');
      child.uom = values.uom;
      child.gold_weight = values.gold_weight;
      child.making_chargein_percentage = values.making_charge_in_percentage;
      child.stone = stone_names;
      child.individual_stone_weight = stone_weight;
      child.stone_weight = values.total_stone_weight;
      child.unit_stone_charge = values.unit_stone_charge;
      for (let i = 0; i < values.stone_details.length; i++) {
          let stone_charge = values.unit_stone_charge * values.total_stone_weight;
          frappe.model.set_value(child.doctype, child.name, 'stone_charge', stone_charge);
      }
      let amount_without_making_charge = (values.gold_weight * frm.doc.board_rate) + stone_charge;
      frappe.model.set_value(child.doctype, child.name, 'amount_without_making_charge', amount_without_making_charge);
      let making_charge = amount_without_making_charge * (child.making_chargein_percentage / 100);
      frappe.model.set_value(child.doctype, child.name, 'making_charge', making_charge);
      refresh_field("item_details");
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

frappe.ui.form.on("Jewellery Item Receipt", {
    item_details_add: function(frm, cdt, cdn) {
        let child = locals[cdt][cdn];
        if (frm.doc.stone) {
            frappe.model.set_value(child.doctype, child.name, 'stone', frm.doc.stone);
            frappe.model.set_value(child.doctype, child.name, 'has_stone', frm.doc.has_stone);
            frm.refresh_fields();
        }
        else{
          frappe.model.set_value(child.doctype, child.name, 'has_stone', 0);
        }
    },
    form_render	: function(frm, cdt, cdn) {
        let d = locals[cdt][cdn];
        if (frm.doc.has_stone) {
            let net_weight = d.gold_weight + d.stone_weight;
            frappe.model.set_value(cdt, cdn, 'net_weight', net_weight);
        }
    },
    stone_weight: function(frm, cdt, cdn){
      let d = locals[cdt][cdn];
      if (frm.doc.has_stone){
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
      }
      frm.fields_dict.item_details.grid.toggle_enable('has_stone', frm.doc.has_stone);
      update_calculations_for_row(d, frm);
    },
    gold_weight: function(frm, cdt, cdn) {
      let d = locals[cdt][cdn];
      if (!frm.doc.has_stone) {
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
        update_calculations_for_row(d, frm);
    },
    stone_charge : function(frm, cdt, cdn){
      let d = locals[cdt][cdn];
      if (frm.doc.has_stone){
        let amount_without_making_charge = (d.gold_weight * frm.doc.board_rate) + d.stone_charge
        frappe.model.set_value(cdt, cdn, 'amount_without_making_charge', amount_without_making_charge);
      }
    }
});
