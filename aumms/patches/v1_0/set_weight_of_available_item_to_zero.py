import frappe


def execute():
	'''
		Patch to fill in the Jewellery Orders whose weight of available item was never set.

		The field used to be a Data field, so an order that was saved before anything was
		available holds NULL rather than a figure. It is a weight, and is now held as a
		Float, and MariaDB refuses to cast a NULL into a column that is NOT NULL, so the
		rows are filled in here before the schema is synced.
	'''
	if not frappe.db.table_exists('Jewellery Order'):
		return

	if not frappe.db.has_column('Jewellery Order', 'weight_of_available_item'):
		return

	# no timestamp is touched, an order that never had a figure was never edited
	frappe.db.sql('''
		update `tabJewellery Order`
		set weight_of_available_item = 0
		where weight_of_available_item is null or trim(weight_of_available_item) = ''
	''')
