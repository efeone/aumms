# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from erpnext.accounts.party import get_party_account
from erpnext.setup.doctype.item_group.item_group import get_item_group_defaults
from erpnext.stock.doctype.item.item import get_item_defaults
from frappe.contacts.doctype.address.address import get_company_address
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.model.utils import get_fetch_values
from frappe.utils import cint, flt, money_in_words, rounded

class JewelleryInvoice(Document):
	def validate(self):
		self.set_item_amounts()
		self.set_taxes_and_charges()
		self.set_total_amount()

	def on_submit(self):
		''' Method to Create Sales Order & Purchase Order and link them with Jewellery Invoice '''
		if self.transaction_type in ['Sales', 'Exchange']:
			sales_order = create_sales_order(self.name, self.sales_taxes_and_charges_template)
			if sales_order:
				frappe.db.set_value(self.doctype, self.name, 'sales_order', sales_order)
				self.reload()
			else:
				frappe.throw("Something went wrong while creating Sales Order, Please try again!")

		if self.transaction_type in ['Purchase', 'Exchange'] and self.customer:
			supplier = create_common_party_and_supplier(self.customer)
			if not supplier:
				frappe.throw("Something went wrong while creating Common Party!")
			purchase_receipt = create_purchase_receipt(self.name, supplier)
			if purchase_receipt:
				frappe.db.set_value(self.doctype, self.name, 'purchase_receipt', purchase_receipt)
				self.reload()
				self.validate_common_party_settlement(supplier)
			else:
				frappe.throw("Something went wrong while creating Puchase Receipt, Please try again!")

		# The Purchase Receipt submit hook creates the Purchase Invoice and writes the link
		# back to the database, so reload before the totals are read off self.
		self.reload()
		self.update_settlement()

	def validate_common_party_settlement(self, supplier):
		'''
			Method to make sure the old gold value actually reaches the Customer ledger.

			ERPNext nets the auto created Purchase Invoice into an advance on the Customer
			account, but only when common party accounting is on and the Supplier is the
			secondary side of the Party Link. Without both, the Jewellery Invoice would show
			an amount payable that has no matching entry in the ledger.
		'''
		if not frappe.db.get_single_value('Accounts Settings', 'enable_common_party_accounting'):
			frappe.throw(_('Enable Common Party Accounting in Accounts Settings to settle {0} transactions.').format(self.transaction_type))
		party_link_exists = frappe.db.exists('Party Link', {
			'secondary_role': 'Supplier',
			'secondary_party': supplier
		})
		if not party_link_exists:
			frappe.throw(_('Party Link for Supplier {0} must have the Supplier as the secondary party, otherwise the old gold value is not credited to Customer {1}.').format(supplier, self.customer))

	def before_cancel(self):
		''' Method to stop cancellation while settled Payment Entries are still open '''
		payment_entries = frappe.get_all('Payment Entry', filters={
			'jewellery_invoice': self.name,
			'docstatus': 1
		}, pluck='name')
		if payment_entries:
			frappe.throw(_('Cancel the Payment Entries {0} before cancelling this Jewellery Invoice.').format(', '.join(payment_entries)))

	def on_cancel(self):
		''' On Cancel event of Jewellery Invoice '''
		self.cancel_delivery_note()
		self.cancel_sales_invoice()
		self.cancel_sales_order()
		self.cancel_purchase_invoice()
		self.cancel_purchase_receipt()

	def set_item_amounts(self):
		'''
			Method to price each item from its parts, so the row always adds up.

			A Fixed making charge is an amount held on the item, a Percentage one is worked
			out from the metal value. Applying the percentage formula to a Fixed item
			multiplies by a zero percentage and drops the charge from the price.
		'''
		for item in self.items:
			#The metal value has to be worked out first, a percentage making charge is taken on it
			item.amount_with_out_making_charge = flt(item.board_rate) * flt(item.gold_weight)
			item.net_amount_with_out_making_charge = flt(item.amount_with_out_making_charge) + flt(item.stone_charge)
			if item.making_charge_based_on == 'Fixed':
				item.making_charge = flt(item.is_fixed_making_charge)
			elif item.making_charge_based_on == 'Percentage':
				item.making_charge = flt(item.amount_with_out_making_charge) * flt(item.making_charge_percentage) / 100
			item.amount = flt(item.net_amount_with_out_making_charge) + flt(item.making_charge)
			if item.gold_weight:
				item.rate = flt(item.amount) / flt(item.gold_weight)

	def get_net_total(self):
		''' Method to get the taxable amount, the item amounts less any discount '''
		total_gold_amount = sum(flt(item.amount) for item in self.items)
		return flt(total_gold_amount - flt(self.get('discount_amount')), self.precision('grand_total'))

	def set_taxes_and_charges(self):
		'''
			Method to calculate the taxes from the selected template.

			Calculated on the server so the tax rows are correct even when the document is
			made outside the form, and so they agree with what the Sales Order works out
			from the same template.
		'''
		self.set('custom_sales_taxes_and_charges', [])
		for tax in get_taxes_and_charges(self.sales_taxes_and_charges_template, self.get_net_total()):
			self.append('custom_sales_taxes_and_charges', tax)
		self.custom_total_taxes_and_charges = flt(
			sum(flt(tax.tax_amount) for tax in self.get('custom_sales_taxes_and_charges')),
			self.precision('grand_total')
		)

	def set_total_amount(self):
		''' Method to calculate and set totals '''
		precision = self.precision('grand_total')
		self.total_making_charge = flt(sum(flt(item.making_charge) for item in self.items), precision)
		self.grand_total = flt(self.get_net_total() + flt(self.custom_total_taxes_and_charges), precision)
		if self.disable_rounded_total:
			self.rounded_total = self.grand_total
			self.rounding_adjustment = 0
		else:
			self.rounded_total = rounded(self.grand_total)
			#Only the difference made by rounding belongs here, nothing else
			self.rounding_adjustment = flt(self.rounded_total - self.grand_total, precision)
		self.in_words = money_in_words(self.rounded_total, self.currency)

	def get_settlement_tolerance(self):
		''' Method to get the amount below which a settlement counts as closed '''
		return 0.5 / (10 ** self.precision('outstanding_amount'))

	def get_sales_total(self):
		'''
			Method to get the gross amount receivable from the Customer.

			Read from the submitted Sales Invoice or Sales Order in preference to this
			document, because those are what the customer is actually billed against.
		'''
		for doctype, docname in [('Sales Invoice', self.sales_invoice), ('Sales Order', self.sales_order)]:
			if not docname or not frappe.db.exists(doctype, docname):
				continue
			totals = frappe.db.get_value(doctype, docname, ['docstatus', 'disable_rounded_total', 'grand_total', 'rounded_total'], as_dict=True)
			if totals.docstatus == 1:
				return flt(totals.grand_total if totals.disable_rounded_total else (totals.rounded_total or totals.grand_total))
		return flt(self.grand_total if self.disable_rounded_total else (self.rounded_total or self.grand_total))

	def get_purchase_total(self):
		'''
			Method to get the gross amount payable to the Customer for old gold.

			The Purchase Invoice is preferred because it is the amount ERPNext credited to
			the Customer account, so the Jewellery Invoice and the ledger stay in step.
		'''
		for doctype, docname in [('Purchase Invoice', self.purchase_invoice), ('Purchase Receipt', self.purchase_receipt)]:
			if not docname or not frappe.db.exists(doctype, docname):
				continue
			totals = frappe.db.get_value(doctype, docname, ['docstatus', 'disable_rounded_total', 'grand_total', 'rounded_total'], as_dict=True)
			if totals.docstatus == 1:
				return flt(totals.grand_total if totals.disable_rounded_total else (totals.rounded_total or totals.grand_total))
		return flt(self.total_old_gold_amount)

	def get_settled_amount(self):
		''' Method to get the net cash settled through Payment Entries, positive when received '''
		payment_entries = frappe.get_all('Payment Entry', filters={
			'jewellery_invoice': self.name,
			'docstatus': 1
		}, fields=['payment_type', 'paid_amount', 'received_amount'])
		return sum(
			flt(entry.received_amount) if entry.payment_type == 'Receive' else -flt(entry.paid_amount)
			for entry in payment_entries
		)

	def update_settlement(self):
		'''
			Method to recalculate the settlement against the linked Sales and Purchase documents.

			This is the only writer of net_amount, paid_amount, outstanding_amount and status.
			A positive outstanding is receivable from the Customer, a negative one is payable.
		'''
		precision = self.precision('outstanding_amount')
		net_amount = flt(self.get_sales_total() - self.get_purchase_total(), precision)
		settled_amount = flt(self.get_settled_amount(), precision)
		outstanding_amount = flt(net_amount - settled_amount, precision)
		self.db_set({
			'net_amount': net_amount,
			'paid_amount': settled_amount,
			'outstanding_amount': outstanding_amount,
			'status': self.get_settlement_status(net_amount, settled_amount, outstanding_amount)
		})

	def get_settlement_status(self, net_amount, settled_amount, outstanding_amount):
		''' Method to get the status for a settlement, keeping the milestone until cash moves '''
		if self.docstatus != 1:
			return self.status
		tolerance = self.get_settlement_tolerance()
		if outstanding_amount > tolerance:
			# Customer owes us
			if settled_amount > tolerance:
				return 'Partly Paid' if self.sales_invoice else 'Advance Received'
			return self.get_milestone_status()
		if outstanding_amount < -tolerance:
			# We owe the Customer
			return 'Partly Refunded' if settled_amount < -tolerance else 'To Pay'
		if net_amount > tolerance:
			return 'Paid'
		if net_amount < -tolerance:
			return 'Refunded'
		return self.get_milestone_status()

	def get_milestone_status(self):
		'''
			Method to get the status from how far the documents have progressed.

			The sales side is checked first because an Exchange gets its Purchase Invoice
			as soon as it is submitted, which would otherwise hide the Ordered stage.
		'''
		if self.delivered or self.delivery_note:
			return 'Delivered'
		if self.sales_invoice:
			return 'Invoiced'
		if self.sales_order:
			return 'Ordered'
		if self.purchase_invoice:
			return 'Invoiced'
		return self.status

	def cancel_sales_order(self):
		''' Method to Cancel Sales Order linked with Jewellery Invoice '''
		if self.sales_order:
			if frappe.db.exists('Sales Order', self.sales_order):
				sales_order_doc = frappe.get_doc('Sales Order', self.sales_order)
				if sales_order_doc.docstatus == 1:
					sales_order_doc.cancel()
			else:
				frappe.throw('Sales Order `{0}` not found!'.format(self.sales_order))

	def cancel_purchase_receipt(self):
		''' Method to Cancel Purchase Receipt linked with Jewellery Invoice '''
		if self.purchase_receipt:
			if frappe.db.exists('Purchase Receipt', self.purchase_receipt):
				purchase_receipt_doc = frappe.get_doc('Purchase Receipt', self.purchase_receipt)
				if purchase_receipt_doc.docstatus == 1:
					purchase_receipt_doc.cancel()
			else:
				frappe.throw('Purchase Receipt `{0}` not found!'.format(self.purchase_receipt))

	def cancel_purchase_invoice(self):
		''' Method to Cancel Purchase Invoice linked with Jewellery Invoice '''
		if self.purchase_invoice:
			if frappe.db.exists('Purchase Invoice', self.purchase_invoice):
				purchase_invoice_doc = frappe.get_doc('Purchase Invoice', self.purchase_invoice)
				if purchase_invoice_doc.docstatus == 1:
					purchase_invoice_doc.cancel()
			else:
				frappe.throw('Purchase Invoice `{0}` not found!'.format(self.purchase_invoice))

	def cancel_sales_invoice(self):
		''' Method to Cancel Sales Invoice linked with Jewellery Invoice '''
		if self.sales_invoice:
			if frappe.db.exists('Sales Invoice', self.sales_invoice):
				sales_invoice_doc = frappe.get_doc('Sales Invoice', self.sales_invoice)
				if sales_invoice_doc.docstatus == 1:
					sales_invoice_doc.cancel()
			else:
				frappe.throw('Sales Invoice `{0}` not found!'.format(self.sales_invoice))

	def cancel_delivery_note(self):
		''' Method to Cancel Delivery Note linked with Jewellery Invoice '''
		if self.delivery_note:
			if frappe.db.exists('Delivery Note', self.delivery_note):
				delivery_note_doc = frappe.get_doc('Delivery Note', self.delivery_note)
				if delivery_note_doc.docstatus == 1:
					delivery_note_doc.cancel()
			else:
				frappe.throw('Delivery Note `{0}` not found!'.format(self.delivery_note))

def create_sales_order(source_name, sales_taxes_and_charges_template , target_doc=None):
	''' Method to create Sales Order from Jewellery Invoice '''
	def set_missing_values(source, target):
		keep_metal_ledger = 0
		transaction_type = frappe.db.get_value('Jewellery Invoice', source_name, 'transaction_type')
		if transaction_type in ['Purchase', 'Exchange']:
			keep_metal_ledger = 1
		target.keep_metal_ledger = keep_metal_ledger
		if sales_taxes_and_charges_template:
			taxes_and_charges_details = frappe.get_doc("Sales Taxes and Charges Template", sales_taxes_and_charges_template)
			for tax in taxes_and_charges_details.taxes:
				target.append("taxes", {
					"charge_type": tax.charge_type,
					"account_head": tax.account_head,
					"description": tax.description,
					"rate": tax.rate,
					"tax_amount": tax.tax_amount,
					"included_in_print_rate": tax.included_in_print_rate
				})
	target_doc = get_mapped_doc("Jewellery Invoice", source_name,
		{
			"Jewellery Invoice": {
				"doctype": "Sales Order",
				"field_map": {
				},
			},
			"Jewellery Invoice Item": {
				"doctype": "Sales Order Item",
				"field_map": {
					'delivery_date': 'delivery_date',
					'gold_weight': 'qty',
				},
			},
		}, target_doc, set_missing_values)
	# Carry over the discount entered on the Jewellery Invoice. rounding_adjustment is not a
	# discount and must not be used as one, or the making charge is given away to the customer.
	discount_amount = frappe.db.get_value('Jewellery Invoice', source_name, 'discount_amount')
	if discount_amount:
		target_doc.apply_discount_on = 'Net Total'
		target_doc.discount_amount = discount_amount
	target_doc.submit()
	frappe.msgprint(('Sales Order created'), indicator="green", alert=1)
	frappe.db.commit()
	return target_doc.name

def get_party_link_if_exist(party_type, party):
	''' Method to get Common Party Link if exists '''
	query = """
		SELECT
			CASE
				WHEN primary_role = %(party_type)s THEN secondary_party
				WHEN secondary_role = %(party_type)s THEN primary_party
			END AS party
		FROM
			`tabParty Link`
		WHERE
			(primary_role = %(party_type)s AND primary_party = %(party)s ) OR (secondary_role = %(party_type)s AND secondary_party = %(party)s )
	"""
	party_link = frappe.db.sql(query, { 'party_type':party_type, 'party':party }, as_dict = 1)

	if not party_link:
		# Return None if party link is not set
		return None
	else:
		return party_link[0].party


def create_common_party_and_supplier(customer):
	''' Method to create Supplier against customer and link as Common Party '''
	common_party = get_party_link_if_exist('Customer', customer)
	if not common_party:
		#create supplier for common party
		supplier_doc = frappe.new_doc('Supplier')
		customer_name =  frappe.db.get_value('Customer', customer, 'customer_name')
		supplier_doc.supplier_name = customer_name
		supplier_group = frappe.db.get_single_value('Buying Settings','supplier_group')
		if not supplier_group:
			frappe.throw('Default Supplier Group is not configured in Buying Settigns!')
		supplier_doc.supplier_group = supplier_group
		supplier_doc.insert()
		#link common party
		if supplier_doc.name:
			link_doc = frappe.new_doc('Party Link')
			link_doc.primary_role = 'Customer'
			link_doc.primary_party = customer
			link_doc.secondary_role = 'Supplier'
			link_doc.secondary_party = supplier_doc.name
			link_doc.insert()
		frappe.msgprint(('Common Party and Supplier Created and Link'), indicator="green", alert=1)
		common_party = supplier_doc.name
	return common_party


def create_purchase_receipt(source_name, supplier, target_doc=None):
	''' Method to create Purchase Receipt from Jewellery Invoice '''
	def set_missing_values(source, target):
		target.supplier = supplier
		target.keep_metal_ledger = 1
		target.create_invoice_on_submit = 1
	target_doc = get_mapped_doc("Jewellery Invoice", source_name,
		{
			"Jewellery Invoice": {
				"doctype": "Purchase Receipt",
				"field_map":{
					'transaction_date':'posting_date'
				},
				# discount_amount is a custom field here and holds a sales side stone charge
				# discount, so it must not be mapped to the Purchase Receipt
				"field_no_map": ['discount_amount'],
			},
			"Old Jewellery Item": {
				"doctype": "Purchase Receipt Item",
				"field_map": {
					'item_code':'item_code',
					'weight':'received_qty',
					'weight':'qty'  # noqa: F601
				},
			},
		}, target_doc, set_missing_values)
	target_doc.save()
	#To set Purchase Receipt link in Jewellery Invoice before submition of Purchase Receipt
	frappe.db.set_value('Jewellery Invoice', source_name, 'purchase_receipt', target_doc.name)
	target_doc.submit()
	frappe.msgprint(('Purchase Receipt created'), indicator="green", alert=1)
	frappe.db.commit()
	return target_doc.name

@frappe.whitelist()
def recalculate_settlement(jewellery_invoice):
	''' Method to recalculate the settlement of a Jewellery Invoice from its linked documents '''
	frappe.get_doc('Jewellery Invoice', jewellery_invoice).update_settlement()

def backfill_settlement():
	'''
		Method to bring Jewellery Invoices created before settlement tracking up to date.

		Payment Entries made earlier carry no Jewellery Invoice link, so they are matched
		back through the Sales Order or Sales Invoice they were allocated to first.
		Without that step every earlier payment would read as unpaid.
	'''
	linked_count = 0
	for reference_doctype, reference_field in [('Sales Invoice', 'sales_invoice'), ('Sales Order', 'sales_order')]:
		references = frappe.get_all('Payment Entry Reference', filters={
			'reference_doctype': reference_doctype,
			'docstatus': 1
		}, fields=['parent', 'reference_name'])
		for reference in references:
			if frappe.db.get_value('Payment Entry', reference.parent, 'jewellery_invoice'):
				continue
			jewellery_invoice = frappe.db.get_value('Jewellery Invoice', { reference_field: reference.reference_name })
			if jewellery_invoice:
				frappe.db.set_value('Payment Entry', reference.parent, 'jewellery_invoice', jewellery_invoice, update_modified=False)
				linked_count += 1

	invoice_names = frappe.get_all('Jewellery Invoice', filters={'docstatus': 1}, pluck='name')
	for invoice_name in invoice_names:
		try:
			frappe.get_doc('Jewellery Invoice', invoice_name).update_settlement()
		except Exception:
			frappe.log_error(title='Jewellery Invoice settlement backfill failed', message=invoice_name)
	frappe.db.commit()
	print('Linked {0} Payment Entries and recalculated {1} Jewellery Invoices'.format(linked_count, len(invoice_names)))

def get_sales_reference(doc):
	'''
		Method to get the document a received payment should be allocated against.

		Returns the doctype, name and the amount still open on it, or None when there is
		nothing to allocate to and the payment has to stay as a Customer advance.
	'''
	if doc.sales_invoice and frappe.db.exists('Sales Invoice', doc.sales_invoice):
		invoice = frappe.db.get_value('Sales Invoice', doc.sales_invoice, ['docstatus', 'outstanding_amount'], as_dict=True)
		if invoice.docstatus == 1:
			return frappe._dict({
				'doctype': 'Sales Invoice',
				'name': doc.sales_invoice,
				'outstanding': flt(invoice.outstanding_amount)
			})
	if doc.sales_order and frappe.db.exists('Sales Order', doc.sales_order):
		order = frappe.db.get_value('Sales Order', doc.sales_order, ['docstatus', 'disable_rounded_total', 'grand_total', 'rounded_total', 'advance_paid'], as_dict=True)
		if order.docstatus == 1:
			total = flt(order.grand_total if order.disable_rounded_total else (order.rounded_total or order.grand_total))
			return frappe._dict({
				'doctype': 'Sales Order',
				'name': doc.sales_order,
				'outstanding': total - flt(order.advance_paid)
			})
	return None

def get_mode_of_payment_account(mode_of_payment, company):
	''' Method to get the account of a Mode of Payment for a Company '''
	account = frappe.db.get_value('Mode of Payment Account', {
		'parent': mode_of_payment,
		'company': company
	}, 'default_account')
	if not account:
		frappe.throw(_('Set a Default Account for Mode of Payment {0} in Company {1}.').format(mode_of_payment, company))
	return account

@frappe.whitelist()
def create_payment_entry(mode_of_payment, amount, docname, posting_date=None, reference_no=None, reference_date=None):
	'''
		Method to settle a Jewellery Invoice against the Customer account.

		The sign of the outstanding decides the direction: a positive outstanding is
		received from the Customer and allocated to the Sales Invoice or Sales Order,
		a negative one is paid back to the Customer for old gold taken in excess.
	'''
	if not frappe.db.exists('Jewellery Invoice', docname):
		frappe.throw(_('Jewellery Invoice `{0}` not found!').format(docname))
	if not frappe.db.exists('Mode of Payment', mode_of_payment):
		frappe.throw(_('Mode of Payment `{0}` not found!').format(mode_of_payment))

	doc = frappe.get_doc('Jewellery Invoice', docname)
	if doc.docstatus != 1:
		frappe.throw(_('Jewellery Invoice {0} must be submitted before a payment can be made.').format(docname))

	# Recalculate first so a stale stored value can never authorise an over payment
	doc.update_settlement()

	amount = flt(amount, doc.precision('outstanding_amount'))
	if amount <= 0:
		frappe.throw(_('Payment Amount must be greater than zero.'))

	tolerance = doc.get_settlement_tolerance()
	outstanding_amount = flt(doc.outstanding_amount)
	if abs(outstanding_amount) <= tolerance:
		frappe.throw(_('There is nothing left to settle on {0}.').format(docname))
	if amount > abs(outstanding_amount) + tolerance:
		frappe.throw(_('Payment Amount {0} cannot exceed the outstanding amount {1}.').format(amount, abs(outstanding_amount)))

	payment_type = 'Receive' if outstanding_amount > 0 else 'Pay'
	party_account = get_party_account('Customer', doc.customer, doc.company)
	mode_of_payment_account = get_mode_of_payment_account(mode_of_payment, doc.company)

	payment_entry_doc = frappe.new_doc('Payment Entry')
	payment_entry_doc.payment_type = payment_type
	payment_entry_doc.company = doc.company
	payment_entry_doc.mode_of_payment = mode_of_payment
	payment_entry_doc.party_type = 'Customer'
	payment_entry_doc.party = doc.customer
	payment_entry_doc.paid_amount = amount
	payment_entry_doc.received_amount = amount
	payment_entry_doc.reference_no = reference_no
	payment_entry_doc.reference_date = reference_date
	payment_entry_doc.jewellery_invoice = docname
	if posting_date:
		payment_entry_doc.posting_date = posting_date

	if payment_type == 'Receive':
		payment_entry_doc.paid_from = party_account
		payment_entry_doc.paid_to = mode_of_payment_account
		# Allocate only what the reference can absorb, the rest stays as a Customer advance.
		# total_amount and outstanding_amount are left out because Payment Entry overwrites
		# them from the reference in set_missing_ref_details.
		reference = get_sales_reference(doc)
		if reference and reference.outstanding > tolerance:
			payment_entry_doc.append('references', {
				'reference_doctype': reference.doctype,
				'reference_name': reference.name,
				'allocated_amount': min(amount, reference.outstanding)
			})
	else:
		payment_entry_doc.paid_from = mode_of_payment_account
		payment_entry_doc.paid_to = party_account
		# No references. The old gold sits on the Customer account as a credit raised by the
		# common party Journal Entry, and ERPNext cannot allocate a Payment Entry to it.
		# This posts the matching debit, which Payment Reconciliation can match later.

	payment_entry_doc.insert(ignore_permissions=True)
	payment_entry_doc.submit()
	doc.update_settlement()
	frappe.msgprint(_('Payment Entry created'), indicator='green', alert=1)
	return payment_entry_doc.name

@frappe.whitelist()
def create_sales_invoice(source_name, jewellery_invoice, sales_taxes_and_charges_template = None, keep_metal_ledger = 0, update_stock=0, target_doc=None):
	''' Method to create Sales Invoice from Jewellery Invoice with Sales Order reference '''
	def postprocess(source, target):
		set_missing_values(source, target)

	def set_missing_values(source, target):
		target.flags.ignore_permissions = True
		target.run_method("set_missing_values")
		target.run_method("set_po_nos")
		target.run_method("calculate_taxes_and_totals")

		if source.company_address:
			target.update({"company_address": source.company_address})
		else:
			# set company address
			target.update(get_company_address(target.company))

		if target.company_address:
			target.update(get_fetch_values("Sales Invoice", "company_address", target.company_address))

		target.debit_to = get_party_account("Customer", source.customer, source.company)
		target.allocate_advances_automatically = 1
		target.update_stock = update_stock
		target.taxes_and_charges = sales_taxes_and_charges_template
		target.keep_metal_ledger = 1

		# Fetch Sales Taxes and Charges Template details and set them in Sales Invoice
		# taxes_and_charges_details = frappe.get_doc("Sales Taxes and Charges Template", sales_taxes_and_charges_template)
		# for tax in taxes_and_charges_details.taxes:
		#     target.append("taxes", {
		#         "charge_type": tax.charge_type,
		#         "account_head": tax.account_head,
		#         "description": tax.description,
		#         "rate": tax.rate,
		#         "tax_amount": tax.tax_amount,
		#         "included_in_print_rate": tax.included_in_print_rate
		#     })

	def update_item(source, target, source_parent):
		target.amount = flt(source.amount) - flt(source.billed_amt)
		target.base_amount = target.amount * flt(source_parent.conversion_rate)
		target.qty = (
			target.amount / flt(source.rate)
			if (source.rate and source.billed_amt)
			else source.qty - source.returned_qty
		)

		if source_parent.project:
			target.cost_center = frappe.db.get_value("Project", source_parent.project, "cost_center")
		if target.item_code:
			item = get_item_defaults(target.item_code, source_parent.company)
			item_group = get_item_group_defaults(target.item_code, source_parent.company)
			cost_center = item.get("selling_cost_center") or item_group.get("selling_cost_center")

			if cost_center:
				target.cost_center = cost_center

	doclist = get_mapped_doc(
		"Sales Order",
		source_name,
		{
			"Sales Order": {
				"doctype": "Sales Invoice",
				"field_map": {
					"party_account_currency": "party_account_currency",
					"payment_terms_template": "payment_terms_template",
				},
				"field_no_map": ["payment_terms_template"],
				"validation": {"docstatus": ["=", 1]},
			},
			"Sales Order Item": {
				"doctype": "Sales Invoice Item",
				"field_map": {
					"name": "so_detail",
					"parent": "sales_order",
				},
				"postprocess": update_item,
				"condition": lambda doc: doc.qty
				and (doc.base_amount == 0 or abs(doc.billed_amt) < abs(doc.amount)),
			},
			"Sales Taxes and Charges": {"doctype": "Sales Taxes and Charges", "add_if_empty": True},
			"Sales Team": {"doctype": "Sales Team", "add_if_empty": True},
		},
		target_doc,
		postprocess,
	)

	automatically_fetch_payment_terms = cint(
		frappe.db.get_single_value("Accounts Settings", "automatically_fetch_payment_terms")
	)
	if automatically_fetch_payment_terms:
		doclist.set_payment_schedule()

	doclist.set_onload("ignore_price_list", True)
	doclist.save(ignore_permissions=True)
	doclist.submit()
	if doclist:
		frappe.db.set_value('Jewellery Invoice', jewellery_invoice, 'sales_invoice', doclist.name)
		if update_stock:
			frappe.db.set_value('Jewellery Invoice', jewellery_invoice, 'delivered', 1)
		#Let the settlement set the status, so an amount still owed to the customer is not hidden
		recalculate_settlement(jewellery_invoice)
		frappe.msgprint(('Sales Invoice created'), indicator="green", alert=1)
		return True

@frappe.whitelist()
def get_board_rate(old_item, transaction_date):
	# Fetch the boardrate from the 'Board Rate' doctype
	board_rate = frappe.db.get_value('Board Rate', {'old_item': old_item, 'valid_from': ('<=', transaction_date)},
									 'board_rate', order_by='valid_from desc', as_dict=True)
	print(board_rate)

	return {'board_rate': board_rate}


@frappe.whitelist()
def create_delivery_note(source_name, jewellery_invoice, target_doc=None):
	''' Method to create Delivery Note from Jewellery Invoice with Sales Invoice reference '''
	def set_missing_values(source, target):
		target.run_method("set_missing_values")
		target.run_method("set_po_nos")
		target.run_method("calculate_taxes_and_totals")

	def update_item(source_doc, target_doc, source_parent):
		target_doc.qty = flt(source_doc.qty) - flt(source_doc.delivered_qty)
		target_doc.stock_qty = target_doc.qty * flt(source_doc.conversion_factor)

		target_doc.base_amount = target_doc.qty * flt(source_doc.base_rate)
		target_doc.amount = target_doc.qty * flt(source_doc.rate)

	doclist = get_mapped_doc(
		"Sales Invoice",
		source_name,
		{
			"Sales Invoice": {"doctype": "Delivery Note", "validation": {"docstatus": ["=", 1]}},
			"Sales Invoice Item": {
				"doctype": "Delivery Note Item",
				"field_map": {
					"name": "si_detail",
					"parent": "against_sales_invoice",
					"serial_no": "serial_no",
					"sales_order": "against_sales_order",
					"so_detail": "so_detail",
					"cost_center": "cost_center",
				},
				"postprocess": update_item,
				"condition": lambda doc: doc.delivered_by_supplier != 1,
			},
			"Sales Taxes and Charges": {"doctype": "Sales Taxes and Charges", "add_if_empty": True},
			"Sales Team": {
				"doctype": "Sales Team",
				"field_map": {"incentives": "incentives"},
				"add_if_empty": True,
			},
		},
		target_doc,
		set_missing_values,
	)

	doclist.set_onload("ignore_price_list", True)
	doclist.submit()
	if doclist:
		frappe.db.set_value('Jewellery Invoice', jewellery_invoice, 'delivery_note', doclist.name)
		frappe.db.set_value('Jewellery Invoice', jewellery_invoice, 'delivered', 1)
		#Let the settlement set the status, so an amount still owed to the customer is not hidden
		recalculate_settlement(jewellery_invoice)
		frappe.msgprint(('Delivery Note created'), indicator="green", alert=1)
		return True

def get_taxes_and_charges(sales_taxes_and_charges_template, net_total):
	'''
		Method to work out the tax rows of a template against a net total.

		Mirrors how the Sales Order and Sales Invoice charge the same template, so the
		Jewellery Invoice shows the tax the customer is going to be billed.
	'''
	taxes = []
	net_total = flt(net_total)
	cumulative_total = net_total
	if not sales_taxes_and_charges_template:
		return taxes
	if not frappe.db.exists('Sales Taxes and Charges Template', sales_taxes_and_charges_template):
		return taxes

	template = frappe.get_doc('Sales Taxes and Charges Template', sales_taxes_and_charges_template)
	for tax in template.taxes:
		if tax.charge_type == 'Actual':
			tax_amount = flt(tax.tax_amount, 2)
		elif tax.charge_type == 'On Net Total':
			tax_amount = flt((flt(tax.rate) / 100) * net_total, 2)
		else:
			# On Previous Row Amount and On Previous Row Total need the row they point at,
			# which this flat calculation does not carry. Let the sales document work it out.
			frappe.throw(_('Charge type {0} in template {1} is not supported on Jewellery Invoice.').format(tax.charge_type, sales_taxes_and_charges_template))
		cumulative_total += tax_amount
		taxes.append({
			'charge_type': tax.charge_type,
			'account_head': tax.account_head,
			'description': tax.description,
			'rate': tax.rate,
			'tax_amount': tax_amount,
			'included_in_print_rate': tax.included_in_print_rate,
			'total': flt(cumulative_total, 2)
		})
	return taxes

@frappe.whitelist()
def get_sales_taxes_and_charges_details(sales_taxes_and_charges_template, total_gold_amount, jewellery_invoice):
	''' Method to get the tax rows for a template, used by the form to refresh the table '''
	return get_taxes_and_charges(sales_taxes_and_charges_template, total_gold_amount)


@frappe.whitelist()
def get_making_charge(item_code):
    """
    Fetches the making_charge for a given item_code from the AuMMS Item doctype.
    """
    if item_code:
        
        making_charge = frappe.db.get_value('AuMMS Item', {'item_code': item_code}, 'making_charge')
        return making_charge if making_charge else 0
    return 0



@frappe.whitelist()
def get_pricing_rule_and_items(customer):
    """Fetches the discount percentage and items from Pricing Rule Doctype based on Customer"""
    
    pricing_rule = frappe.db.get_list(
        "Pricing Rule",
        filters={"customer": customer, "disable": 0},
        fields=["name", "discount_percentage"],
        limit=1
    )

    if pricing_rule:
        pricing_rule_name = pricing_rule[0].name
        discount_percentage = pricing_rule[0].discount_percentage if pricing_rule[0].discount_percentage else 0

        rule_items = frappe.get_all(
            "Pricing Rule Item Code",
            filters={"parent": pricing_rule_name},
            fields=["item_code"]
        )

        # Return the discount percentage and the list of item codes
        return {
            "discount_percentage": discount_percentage,
            "rule_items": rule_items
        }
    
    return {}

