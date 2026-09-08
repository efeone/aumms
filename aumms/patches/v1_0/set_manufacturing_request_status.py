import frappe


def execute():
	'''
		Patch to say how far the requests made before there was a status have got.

		The status column is added with Pending against every row, which is only right for
		the requests nobody has started. Each of them is read through its own controller so
		the rule stays in one place, and the timestamp is left alone, a request not having
		been touched by anyone.
	'''
	for name in frappe.get_all('Manufacturing Request', pluck = 'name'):
		request = frappe.get_doc('Manufacturing Request', name)
		frappe.db.set_value(
			'Manufacturing Request', name, 'status', request.get_status(), update_modified = False
		)
