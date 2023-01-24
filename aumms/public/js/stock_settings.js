frappe.ui.form.on('Stock Settings', {
    refresh(frm) {
        // set auto_insert_price_list_rate_if_missing field property hidden as 1
        frm.set_df_property('auto_insert_price_list_rate_if_missing', 'hidden', 1)
    }
});