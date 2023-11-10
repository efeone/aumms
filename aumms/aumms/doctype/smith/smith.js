// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Smith', {
	refresh:function(frm) {
		set_head_of_smith_filter_query(frm)
	},
	smith_type: function(frm) {
		reset_smith_fields(frm)
		set_smith_reference_filter_query(frm)
	},
	employee: function(frm) {
		set_smith_full_name(frm)
		set_department(frm)
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
	frm.set_value('department', '')
	frm.set_df_property('department', 'read_only', 0)
	frm.refresh_fields()
}

function set_head_of_smith_filter_query(frm) {
	// set filter for head of smith field, only head of smith employees will be listed
	frm.set_query('head_of_smith', () => {
		return {
			query: 'aumms.aumms.doctype.smith.smith.head_of_smith_filter_query'
		}
	})
}

function set_smith_reference_filter_query(frm) {
	// set filter for employee and supplier fields, exclude those with Smith already created
	let fieldname = 'employee'
	if (frm.doc.smith_type == 'External') {
		fieldname = 'supplier'
	}
	frm.set_query(fieldname, () => {
		return {
			query: 'aumms.aumms.doctype.smith.smith.smith_reference_filter_query'
		}
	})
}

function set_department(frm) {
	// fetch department and set the field as read only if smith type is internal and employee is selected
	if (frm.doc. employee){
		frappe.db.get_value('Employee', frm.doc.employee, 'department')
			.then(r => {
				let department = r.message.department
				frm.set_value('department', department)
				frm.set_df_property('department', 'read_only', 1)
				frm.refresh_fields()
			})
	}
}
