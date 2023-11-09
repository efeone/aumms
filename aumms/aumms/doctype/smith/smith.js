// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Smith', {
	smith_type: function(frm) {
		reset_smith_fields(frm)
	},
	employee: function(frm) {
		set_smith_full_name(frm)
	},
	supplier:  function(frm) {
		set_smith_full_name(frm)
	}
});

function set_smith_full_name(frm) {
	// Fetching a smith's name from employee or supplier depending on the type
	if (frm.doc.smith_type == 'Internal') {
		frappe.db.get_value('Employee', frm.doc.employee, 'employee_name')
			.then(r => {
				let smith_full_name = r.message.employee_name
				frm.set_value('smith_name', smith_full_name)
			})
	}
	else if (frm.doc.smith_type == 'External') {
		frappe.db.get_value('Supplier', frm.doc.supplier, 'supplier_name')
			.then(r => {
				let smith_full_name = r.message.supplier_name
				frm.set_value('smith_name', smith_full_name)
				frm.refresh_fields()
			})
	}
}

function reset_smith_fields(frm) {
	// Resetting the fields when smith type is changed
	frm.set_value('smith_name', '')
	frm.set_value('employee', '')
	frm.set_value('supplier', '')
	frm.refresh_fields()
}
