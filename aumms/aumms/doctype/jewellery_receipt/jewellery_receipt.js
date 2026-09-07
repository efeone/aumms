frappe.ui.form.on("Jewellery Receipt", {
  setup: function (frm) {
    frm.set_query("uom", "item_details", () => {
      return {
        filters: {
          is_purity_uom: 1,
        },
      };
    });
  },
  refresh: function (frm) {
    frm.fields_dict["item_wise_stone_details"].grid.wrapper.on(
    "click",
    ".grid-remove-row",
    function () {
      setTimeout(() => {
        update_stone_weight_and_charge(frm);
      }, 100);
    }
    );
    frm.set_query("stone", "item_details", () => {
      return {
        filters: {
          is_stone_item: 1,
        },
      };
    });
    set_sub_category_filter(frm);
    hide_item_details_add_row(frm);
  },
  onload: function (frm) {
    frm.fields_dict["item_wise_stone_details"].grid.cannot_add_rows = true;
    frm.refresh_field("item_wise_stone_details");
  },
  item_sub_category: function (frm) {
    frm.events.update_item_details_table(frm);
  },
  item_category: function (frm) {
    set_sub_category_filter(frm);
    frm.events.update_item_details_table(frm);
  },
  item_type: function (frm) {
    frm.events.update_item_details_table(frm);
    item_group_filters(frm);
  },
  item_group: function (frm) {
    frm.events.update_item_details_table(frm);
  },
  purity: function (frm) {
    frm.events.update_item_details_table(frm);
  },
  board_rate: function (frm) {
    frm.events.update_item_details_table(frm);
  },
  supplier: function (frm) {
    frm.events.update_item_details_table(frm);
  },
  update_item_details_table: function (frm) {
    if (frm.doc.item_details) {
      let making_charge = 0;

      frappe.db
        .get_value(
          "Item Sub Category",
          frm.doc.item_sub_category,
          "making_charge_in_percentage"
        )
        .then((r) => {
          making_charge = r.message.making_charge_in_percentage;
          const updateItems = () => {
            frm.doc.item_details.forEach(function (item) {
              frappe.model.set_value(
                item.doctype,
                item.name,
                "item_category",
                frm.doc.item_category
              );
              frappe.model.set_value(
                item.doctype,
                item.name,
                "item_type",
                frm.doc.item_type
              );
              frappe.model.set_value(
                item.doctype,
                item.name,
                "item_group",
                frm.doc.item_group
              );
              frappe.model.set_value(
                item.doctype,
                item.name,
                "purity",
                frm.doc.purity
              );
              frappe.model.set_value(
                item.doctype,
                item.name,
                "board_rate",
                frm.doc.board_rate
              );
              frappe.model.set_value(
                item.doctype,
                item.name,
                "making_chargein_percentage",
                making_charge
              );
            });
            frm.refresh_fields();
          };

          updateItems();
        });
    }
  },

  quantity: function (frm) {
    var quantity = frm.doc.quantity;
    var cur_items_len = frm.doc.item_details.length;

    if (quantity < cur_items_len) {
      frm.doc.item_details.splice(quantity);
    } else {
      frappe.db
        .get_value(
          "Item Sub Category",
          frm.doc.item_sub_category,
          "making_charge_in_percentage"
        )
        .then((r) => {
          console.log("here1");
          console.log(cur_items_len);
          console.log(quantity);
          
          
          for (var i = cur_items_len; i < quantity; i++) {
            console.log("loop");
            
            frm.add_child("item_details", {
              item_category: frm.doc.item_category,
              item_type: frm.doc.item_type,
              item_group: frm.doc.item_group,
              purity: frm.doc.purity,
              board_rate: frm.doc.board_rate,
              making_chargein_percentage: r.message.making_charge_in_percentage,
            });
            frm.refresh_fields()
          }
        });
      
    }

    frm.refresh_field("item_details");
  },
});
frappe.ui.form.on("Jewellery Item Receipt", {
  // form_render: function (frm, cdt, cdn) {
  //   let d = locals[cdt][cdn];
  //   if (d.has_stone) {
  //     let net_weight = d.gold_weight + d.stone_weight;
  //     frappe.model.set_value(cdt, cdn, "net_weight", net_weight);
  //   }
  // }, kept for future reference
  stone_weight: function (frm, cdt, cdn) {
    let d = locals[cdt][cdn];
    if (d.single_stone) {
      let net_weight = d.gold_weight + d.stone_weight;
      frappe.model.set_value(cdt, cdn, "net_weight", net_weight);
      let stone_charge = d.unit_stone_charge * d.stone_weight;
      frappe.model.set_value(cdt, cdn, "stone_charge", stone_charge);
    }
  },
  making_charge: function (frm, cdt, cdn) {
    if (d.making_charge) {
      let amount = d.amount_without_making_charge + d.making_charge;
      frappe.model.set_value(cdt, cdn, "amount", amount);
    }
    frm.fields_dict.item_details.grid.toggle_enable(
      "has_stone",
      frm.doc.has_stone
    );
    frm.fields_dict.item_details.grid.toggle_enable(
      "has_stone",
      frm.doc.has_stone
    );
  },
  gold_weight: function (frm, cdt, cdn) {
    let d = locals[cdt][cdn];
    if (!d.has_stone || !d.stone_charge) {
      let net_weight = d.gold_weight;
      frappe.model.set_value(cdt, cdn, "net_weight", net_weight);
      let amount_without_making_charge = d.gold_weight * frm.doc.board_rate;
      frappe.model.set_value(
        cdt,
        cdn,
        "amount_without_making_charge",
        amount_without_making_charge
      );
    }
    if (d.amount_without_making_charge && d.making_chargein_percentage) {
      let making_charge =
        d.amount_without_making_charge * (d.making_chargein_percentage / 100);
      frappe.model.set_value(cdt, cdn, "making_charge", making_charge);
    }
    frm.call("calculate_item_details")
  },
  making_chargein_percentage: function (frm, cdt, cdn) {
    let d = locals[cdt][cdn];
    if (d.amount_without_making_charge && d.making_chargein_percentage) {
      let making_charge =
        d.amount_without_making_charge * (d.making_chargein_percentage / 100);
      frappe.model.set_value(cdt, cdn, "making_charge", making_charge);
    }
  },
  making_charge: function (frm, cdt, cdn) {
    let d = locals[cdt][cdn];
    if (d.making_charge) {
      let amount = d.amount_without_making_charge + d.making_charge;
      frappe.model.set_value(cdt, cdn, "amount", amount);
    }
  },
  stone_charge: function (frm, cdt, cdn) {
    let d = locals[cdt][cdn];
    if (d.has_stone) {
      let amount_without_making_charge =
        d.gold_weight * frm.doc.board_rate + d.stone_charge;
      frappe.model.set_value(
        cdt,
        cdn,
        "amount_without_making_charge",
        amount_without_making_charge
      );
    }
    frm.refresh_field("item_details");
  },
  add_stone: function (frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (row.has_stone) {
    if (!row.stone || !row.stone_uom || !row.stone_weight || !row.rate) {
        frappe.msgprint(__(
          'Please ensure all stone details are filled before adding.'));
        return;
    }

    frm.add_child("item_wise_stone_details", {
        reference: row.idx,
        stone: row.stone,
        uom: row.stone_uom,
        stone_weight: row.stone_weight,
        rate: row.rate,
        amount: row.rate * row.stone_weight,
    });

    frm.refresh_field("item_wise_stone_details");
    } else {
        frappe.msgprint(__('Has Stone must be checked to add a stone.'));
    }

    if (row.stone_weight_gold_weight_uom)
      row.stone_weight_gold_weight_uom += row.stone_weight;
    else row.stone_weight_gold_weight_uom = row.stone_weight;
    row.net_weight += row.stone_weight;
    if (row.stone_charge) row.stone_charge += row.rate * row.stone_weight;
    else row.stone_charge = row.rate * row.stone_weight;

    row.stone = "";
    row.stone_uom = "Gram";
    row.stone_weight = "";
    row.rate = "";

    frm.refresh_field("item_wise_stone_details");
    frm.refresh_field("item_details");
    frm.call("calculate_item_details")
  },
  board_rate: function(frm) {
    frm.call("calculate_item_details")
  }
});

let create_multi_stone = function (frm, cdt, cdn) {
  let d = new frappe.ui.Dialog({
    title: "Enter Stone Details",
    fields: [
      {
        label: "UOM",
        fieldname: "uom",
        fieldtype: "Link",
        options: "UOM",
        reqd: 1,
      },
      {
        label: "Gold Weight",
        fieldname: "gold_weight",
        fieldtype: "Float",
        reqd: 1,
      },
      {
        label: "Making Charge In Percentage",
        fieldname: "making_charge_in_percentage",
        fieldtype: "Percent",
        reqd: 1,
      },
      {
        label: "Stone Details",
        fieldname: "stone_details",
        fieldtype: "Table",
        reqd: 1,
        annotatable: true,
        editable: true,
        fields: [
          {
            label: "Stone",
            fieldname: "stone",
            fieldtype: "Link",
            in_list_view: 1,
            options: "AuMMS Item",
          },
          {
            label: "Stone Weight",
            fieldname: "stone_weight",
            fieldtype: "Float",
            in_list_view: 1,
          },
        ],
      },
      {
        label: "Total Stone Weight",
        fieldname: "total_stone_weight",
        fieldtype: "Float",
      },
      {
        label: "Unit of Stone Charge",
        fieldname: "unit_stone_charge",
        fieldtype: "Int",
        reqd: 1,
      },
    ],
    primary_action_label: "Submit",
    primary_action: function (values) {
      var quantity = frm.doc.quantity;
      for (var i = 0; i < quantity; i++) {
        var child = locals[cdt][cdn];
        if (!child) {
          // If the child at index 'i' doesn't exist, add a new row
          child = frm.add_child("item_details", {
            item_category: frm.doc.item_category,
            item_type: frm.doc.item_type,
            item_group: frm.doc.item_group,
            purity: frm.doc.purity,
            board_rate: frm.doc.board_rate,
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

        let amount_without_making_charge =
          values.gold_weight * frm.doc.board_rate + stone_charge;
        child.amount_without_making_charge = amount_without_making_charge;

        let making_charge =
          amount_without_making_charge *
          (values.making_charge_in_percentage / 100);
        child.making_charge = making_charge;

        let amount = amount_without_making_charge + making_charge;
        child.amount = amount;
      }

      refresh_field("item_details");
      d.hide();
    },
  });

  function calculate_total_stone_weight() {
    let total_weight = 0;
    let stone_details = d.get_value("stone_details");
    if (stone_details && stone_details.length > 0) {
      stone_details.forEach(function (row) {
        total_weight += row.stone_weight || 0;
      });
    }
    d.set_value("total_stone_weight", total_weight);
  }

  document.addEventListener("change", function (event) {
    if (event.target.matches('[data-fieldname="stone_weight"]')) {
      calculate_total_stone_weight();
    }
  });

  if ("stone_details" in d.fields_dict) {
    d.fields_dict.stone_details.grid.get_field("stone").get_query =
      function () {
        return {
          filters: {
            is_stone_item: 1,
          },
        };
      };
  }
  if ("uom" in d.fields_dict) {
    d.fields_dict.uom.get_query = function () {
      return {
        filters: {
          is_purity_uom: 1,
        },
      };
    };
  }
  d.show();
};

function item_group_filters(frm) {
  frm.set_query("item_group", () => {
    return {
      filters: {
        is_aumms_item_group: 1,
        item_type: frm.doc.item_type,
      },
    };
  });
}

function set_sub_category_filter(frm) {
  frm.set_query("item_sub_category", () => {
    return {
      filters: {
        item_category: frm.doc.item_category,
      },
    };
  });
}
frappe.ui.form.on("Item Wise Stone Details", {
  item_wise_stone_details_remove: function (frm, cdt, cdn) {
    update_stone_weight_and_charge(frm);
  },
  stone_weight: function (frm, cdt, cdn) {
  update_stone_weight_and_charge(frm);
  },
  rate: function (frm, cdt, cdn) {
  update_stone_weight_and_charge(frm);
  }
});

function update_stone_weight_and_charge(frm) {
  frm.doc.item_details.forEach((item) => {
    item.stone_weight_gold_weight_uom = 0;
    item.stone_charge = 0;
  });
  frm.doc.item_wise_stone_details.forEach((stone_row) => {
    let parent_row = frm.doc.item_details.find((item) => item.idx === stone_row.reference);
    if (parent_row) {
      parent_row.stone_weight_gold_weight_uom += stone_row.stone_weight;
      parent_row.stone_charge += stone_row.rate * stone_row.stone_weight;
    }
  });
  frm.refresh_field("item_details");
}

//Item rows are generated from the receipt quantity, they are never keyed in by hand
let hide_item_details_add_row = function (frm) {
  let grid = frm.get_field("item_details").grid;
  grid.cannot_add_rows = true;
  grid.refresh();
};
