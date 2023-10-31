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
    }
})
  