import frappe


def execute():
	'''
		Patch to make the pieces already manufactured sellable.

		The item a Jewellery Job Card raises for a piece was left without a weight unit and
		was never marked as sold, so a Jewellery Invoice would neither offer the piece nor
		save a row for it, the unit on a row being read off the item every time it is saved.
		Nor did it carry the making charge the customer agreed to, which is what the invoice
		prices the work at. The job card sets them all from now on, and the pieces made
		before it did are put right here.
	'''
	requests = get_requests_by_product()
	for item in get_manufactured_items(requests):
		request = requests[item.name]
		#the request holds the units the job card should have raised the item with
		weight_uom = item.weight_uom or request.weight_uom or request.uom or item.stock_uom
		sales_uom = item.sales_uom or item.stock_uom
		if not weight_uom:
			#nothing names a unit for this piece, and it is one to be put right by hand
			continue
		set_sales_details(item, weight_uom, sales_uom, get_making_charge_percentage(request))


def get_requests_by_product():
	'''
		Method to get the Manufacturing Request behind each manufactured piece.
		output: dict of the AuMMS Item name and the request that made it

		A request raises an item of its own, so the first request found for a piece is the
		one that made it, and any other would stand on the same units anyway.
	'''
	requests = {}
	for request in frappe.get_all(
		'Manufacturing Request',
		filters = {'product': ['is', 'set']},
		fields = ['product', 'weight_uom', 'uom', 'jewellery_order'],
		order_by = 'creation'
	):
		requests.setdefault(request.product, request)
	return requests


def get_manufactured_items(requests):
	'''
		Method to get the AuMMS Items of the pieces the requests made
		args:
			requests: dict of the AuMMS Item name and the request that made it
		output: list of the AuMMS Items, read in batches, an old shop having made many
	'''
	items = []
	names = list(requests)
	batch_size = 500
	for start in range(0, len(names), batch_size):
		items += frappe.get_all(
			'AuMMS Item',
			filters = {'name': ['in', names[start:start + batch_size]]},
			fields = [
				'name', 'item', 'stock_uom', 'weight_uom', 'sales_uom', 'is_sales_item',
				'making_charge_based_on'
			]
		)
	return items


def get_making_charge_percentage(request):
	'''
		Method to get the making charge the customer agreed to for a piece
		args:
			request: the Manufacturing Request that made the piece
		output: the percentage on the Customer Jewellery Order, else None

		A piece made for stock is charged for by the shop and has no order behind it to
		read a charge off.
	'''
	if not request.jewellery_order:
		return None

	customer_jewellery_order = frappe.db.get_value(
		'Jewellery Order', request.jewellery_order, 'customer_jewellery_order'
	)
	if not customer_jewellery_order:
		return None
	return frappe.db.get_value(
		'Customer Jewellery Order', customer_jewellery_order, 'making_chargein_percentage'
	)


def set_sales_details(item, weight_uom, sales_uom, making_charge_percentage):
	'''
		Method to put the selling details on a piece and on the Item behind it
		args:
			item: the AuMMS Item of the piece
			weight_uom: the unit the piece is weighed in
			sales_uom: the unit the piece is sold in
			making_charge_percentage: the charge the customer agreed to, if there is one

		A piece already priced by the shop keeps the charge it was given, this being a
		correction of what was never filled in rather than a repricing.

		The Item carries the same fields and is written to directly rather than through the
		AuMMS Item, which would turn away a piece that is short of something else. The
		timestamp is left alone, a correction not reading as a user edit.
	'''
	values = {
		'weight_uom': weight_uom,
		'sales_uom': sales_uom,
		'is_sales_item': 1
	}
	if making_charge_percentage and not item.making_charge_based_on:
		values['making_charge_based_on'] = 'Percentage'
		values['making_charge_percentage'] = making_charge_percentage

	frappe.db.set_value('AuMMS Item', item.name, values, update_modified = False)
	if item.item and frappe.db.exists('Item', item.item):
		frappe.db.set_value('Item', item.item, values, update_modified = False)
