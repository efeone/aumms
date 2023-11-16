frappe.ui.form.on('Job Card', {
    refresh(frm) {
        // Set a filter for the 'employee' field
        frm.set_query('employee', function() {
            return {
                filters: {
                    Designation: 'Smith'
                }
            };
        });
        frm.remove_custom_button("Start Job");
    },

    prepare_timer_buttons: function(frm) {
		frm.trigger("make_dashboard");

		if (!frm.doc.started_time && !frm.doc.current_time) {
			frm.add_custom_button(__("Start Job"), () => {
				if ((frm.doc.employee && !frm.doc.employee.length) || !frm.doc.employee) {
					frappe.prompt({fieldtype: 'Link', label: __('Select Employees'),
						options: "Employee", fieldname: 'employees', default:frm.doc.assigned_employee, get_query() {
                            return {
                                filters: {
                                    "designation": "Smith"
                                }
                            };
                        }}, d => {
						frm.events.start_job(frm, "Work In Progress", [{'employee':d.employees}]);
					}, __("Assign Job to Employee"));
				} else {
					frm.events.start_job(frm, "Work In Progress", frm.doc.employee);
				}
			}).addClass("btn-primary");
		} else if (frm.doc.status == "On Hold") {
			frm.add_custom_button(__("Resume Job"), () => {
				frm.events.start_job(frm, "Resume Job", frm.doc.employee);
			}).addClass("btn-primary");
		} else {
			frm.add_custom_button(__("Pause Job"), () => {
				frm.events.complete_job(frm, "On Hold");
			});

			frm.add_custom_button(__("Complete Job"), () => {
				var sub_operations = frm.doc.sub_operations;

				let set_qty = true;
				if (sub_operations && sub_operations.length > 1) {
					set_qty = false;
					let last_op_row = sub_operations[sub_operations.length - 2];

					if (last_op_row.status == 'Complete') {
						set_qty = true;
					}
				}

				if (set_qty) {
					frappe.prompt({fieldtype: 'Float', label: __('Completed Quantity'),
						fieldname: 'qty', default: frm.doc.for_quantity}, data => {
						frm.events.complete_job(frm, "Complete", data.qty);
					}, __("Enter Value"));
				} else {
					frm.events.complete_job(frm, "Complete", 0.0);
				}
			}).addClass("btn-primary");
		}
	},


})
