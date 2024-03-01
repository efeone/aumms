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
    }
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
        options: 'UOM'
      },
      {
        label: 'Gold Weight',
        fieldname: 'gold_weight',
        fieldtype: 'Float'
      },
      {
        label: 'Making Charge In Percentage',
        fieldname: 'making_charge_in_percentage',
        fieldtype: 'Percent',
      },
      {
        label: 'Has Stone',
        fieldname: 'has_stone',
        fieldtype: 'Check'
      },
      {
        label: 'Stone Details',
        fieldname: 'stone_details',
        fieldtype: 'Table',
        reqd: 1,
        annotatable: true,
        editable: true,
        depends_on: 'eval: doc.has_stone',
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
        depends_on: 'eval: doc.has_stone'
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
      let stone_charge = 0
      if (values.has_stone) {
          // Concatenate the names of all stones
          for (let i = 0; i < values.stone_details.length; i++) {
              stone_names += values.stone_details[i].stone;
              if (i < values.stone_details.length - 1) {
                  stone_names += " - ";
              }
          }
      }
      var child = frm.add_child('item_details');
      child.uom = values.uom;
      child.gold_weight = values.gold_weight;
      child.making_chargein_percentage = values.making_charge_in_percentage;
      child.has_stone = values.has_stone;
      child.stone = stone_names;
      child.stone_weight = values.total_stone_weight;
      child.unit_stone_charge = values.unit_stone_charge;
      if (values.has_stone) {
          for (let i = 0; i < values.stone_details.length; i++) {
              let stone_charge = values.unit_stone_charge * values.total_stone_weight;
              frappe.model.set_value(child.doctype, child.name, 'stone_charge', stone_charge);
          }
          let amount_without_making_charge = (values.gold_weight * frm.doc.board_rate) + stone_charge;
          frappe.model.set_value(child.doctype, child.name, 'amount_without_making_charge', amount_without_making_charge);
          let making_charge = amount_without_making_charge * (child.making_chargein_percentage / 100);
          frappe.model.set_value(child.doctype, child.name, 'making_charge', making_charge);
      }

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

  if ('stone' in d.fields_dict) {
    d.fields_dict.stone.get_query = function() {
      return {
        filters: {
          "is_stone_item": 1
        }
      };
    };
  }

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
      }frm.fields_dict.item_details.grid.toggle_enable('has_stone', frm.doc.has_stone);frm.fields_dict.item_details.grid.toggle_enable('has_stone', frm.doc.has_stone);
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
    },
    stone_charge : function(frm, cdt, cdn){
      let d = locals[cdt][cdn];
      if (frm.doc.has_stone){
        let amount_without_making_charge = (d.gold_weight * frm.doc.board_rate) + d.stone_charge
        frappe.model.set_value(cdt, cdn, 'amount_without_making_charge', amount_without_making_charge);
      }
    }
});
