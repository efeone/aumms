frappe.ui.form.on('Item Group', {

    parent_item_group(frm) {

        // set item_type as read and write
        frm.set_df_property('item_type', 'read_only', 0)

        if (frm.doc.parent_item_group) {
            // call to get item type from parent item group
            frappe.db.get_value('Item Group', frm.doc.parent_item_group, 'item_type')
                .then(r => {
                    if (r.message.item_type) {
                        // set item_type as read only
                        frm.set_df_property('item_type', 'read_only', 1)
                    }
                })
        }
    },
    making_charge_based_on(frm) {
      if(frm.doc.making_charge_based_on == 'Fixed'){// set currency = 0 while the change of making_charge_based_on
        frm.refresh_field('currency')
        frm.set_value('currency', 0)
      }
      if(frm.doc.making_charge_based_on == 'Percentage'){// set percentage = 0 while the change of making_charge_based_on
        frm.refresh_field('percentage')
        frm.set_value('percentage', 0)
      }
    }

})
