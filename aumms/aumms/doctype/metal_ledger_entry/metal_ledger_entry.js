// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Metal Ledger Entry', {
	refresh: function(frm) {
    //Disable save button from metal ledger entry
    frm.disable_save();
}
});
