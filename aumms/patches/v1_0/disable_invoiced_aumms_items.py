import frappe


def execute():
	'''
		Patch to flag the jewellery pieces that were already sold before the flag was set.

		A piece is unique and only ever has one in stock, so a piece already billed must
		not be offered on a new Jewellery Invoice. This does to the sales history what
		create_sales_invoice and create_delivery_note now do to a new sale.
	'''
	disable_records('AuMMS Item', get_invoiced_aumms_items())
	disable_records('Item', get_delivered_items())


def get_invoiced_aumms_items():
	'''
		Method to get the AuMMS Items sold on a Jewellery Invoice that is billed.

		Only the Items table is read. Old Jewellery Items are bought in from the customer
		rather than sold, and Stone Details are parts of a piece, not pieces themselves.
	'''
	return frappe.db.sql('''
		select distinct jii.item_code
		from `tabJewellery Invoice Item` jii
		inner join `tabJewellery Invoice` ji
			on ji.name = jii.parent and jii.parenttype = 'Jewellery Invoice'
		inner join `tabSales Invoice` si on si.name = ji.sales_invoice
		where ji.docstatus = 1 and si.docstatus = 1
	''', pluck=True)


def get_delivered_items():
	'''
		Method to get the Items behind the pieces that have already left the shop.

		The Item is only flagged once the piece is delivered, either on a submitted
		Delivery Note or on an invoice that moved the stock itself. ERPNext refuses a
		disabled Item in a selling document, so flagging it earlier would block a delivery
		that is still due.
	'''
	return frappe.db.sql('''
		select distinct ai.item
		from `tabJewellery Invoice Item` jii
		inner join `tabJewellery Invoice` ji
			on ji.name = jii.parent and jii.parenttype = 'Jewellery Invoice'
		inner join `tabSales Invoice` si on si.name = ji.sales_invoice
		inner join `tabAuMMS Item` ai on ai.name = jii.item_code
		left join `tabDelivery Note` dn on dn.name = ji.delivery_note
		where ji.docstatus = 1 and si.docstatus = 1
			and coalesce(ai.item, '') != ''
			and (si.update_stock = 1 or dn.docstatus = 1)
	''', pluck=True)


def disable_records(doctype, names):
	'''
		Method to flag the records in batches, an old shop carries a long sales history.

		The timestamp is left alone. The flag is worked out from the sales documents
		rather than keyed in, so it should not read as a user edit.
	'''
	batch_size = 500
	for start in range(0, len(names), batch_size):
		frappe.db.set_value(doctype, {
			'name': ('in', names[start:start + batch_size]),
			'disabled': 0
		}, 'disabled', 1, update_modified=False)
