// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Purity', {

	purity_percentage (frm) {

		if (frm.doc.purity_percentage) {

			// check purity percentage is not between 0 and 100
			if(0 > frm.doc.purity_percentage || frm.doc.purity_percentage  > 100) {

				// message for user about purity percentage range
				frappe.throw({
					title: __('ALERT !!'),
					message: __('Purity Percentage must range from 0 to 100')
				});

			}
		}

	}

});