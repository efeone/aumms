# Copyright (c) 2026, efeone and contributors
# For license information, please see license.txt
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_link_to_form

from erpnext.accounts.party import get_party_account

from aumms.aumms.doctype.jewellery_invoice.jewellery_invoice import get_mode_of_payment_account
from aumms.aumms.utils import (
	cancel_metal_ledger_entries,
	get_board_rate,
	get_metal_balance_qty,
	repost_metal_ledger_balance,
)


class SmithSettlement(Document):
	def validate(self):
		self.validate_duplicate()
		self.set_company()
		self.set_posting_time()
		self.set_gold_weight()

	def on_submit(self):
		if self.mode_of_settlement == 'Gold':
			self.settle_in_gold()
		else:
			self.settle_in_cash()

	def on_cancel(self):
		self.cancel_payment_entry()
		self.cancel_stock_entry()
		cancel_metal_ledger_entries(self)

	def validate_duplicate(self):
		"""
			method to keep a request to a single settlement

			The button that raises a settlement is taken away once the request has one, so a
			second settlement is a request settled twice rather than a request settled again.
		"""
		if not self.manufacturing_request:
			return

		duplicate = frappe.db.exists('Smith Settlement', {
			'manufacturing_request': self.manufacturing_request,
			'docstatus': ['<', 2],
			'name': ['!=', self.name]
		})
		if duplicate:
			frappe.throw(
				_('{0} is already settled by {1}.').format(
					frappe.bold(self.manufacturing_request),
					get_link_to_form('Smith Settlement', duplicate)
				),
				title = _('Already Settled')
			)

	def set_company(self):
		if not self.company:
			self.company = frappe.defaults.get_defaults().company

	def set_posting_time(self):
		"""
			method to stamp the time the metal ledger reads this settlement at

			A settlement is dated but not timed. Stamping it at the end of the day keeps it
			behind any movement made the same day, so a repost walks the two in the order
			they happened.
		"""
		if not self.posting_time:
			self.posting_time = '23:59:59'

	def set_gold_weight(self):
		"""
			method to price the payable in metal

			A smith paid in gold is paid the weight the money buys on the day, so the board
			rate of the posting date turns the amount into a weight.
		"""
		if self.mode_of_settlement != 'Gold':
			self.board_rate = 0
			self.weight = 0
			return

		if not (self.item_type and self.purity and self.stock_uom):
			return

		self.board_rate = flt(get_board_rate(self.item_type, self.purity, self.stock_uom, self.posting_date))
		if not self.board_rate:
			frappe.throw(
				_('No Board Rate for {0} {1} on {2}, so the payable cannot be turned into a weight.').format(
					frappe.bold(self.purity), frappe.bold(self.item_type), frappe.bold(self.posting_date)
				)
			)
		self.weight = flt(self.payable_amount) / self.board_rate

	def get_smith_party(self):
		"""
			method to get the account a smith is paid through
			output: tuple of the party type and the party

			Only an External smith keeps a Supplier account. An Internal one is an Employee
			and is paid through payroll, which has no party account to post against here.
		"""
		smith = frappe.db.get_value('Smith', self.smith, ['smith_type', 'supplier'], as_dict = 1)
		if smith.smith_type != 'External' or not smith.supplier:
			frappe.throw(
				_('{0} is an {1} smith and keeps no Supplier account, so a cash settlement cannot be posted. Settle in Gold, or pay an Internal smith through payroll.').format(
					frappe.bold(self.smith), frappe.bold(smith.smith_type or _('Internal'))
				),
				title = _('No Supplier Account')
			)
		return 'Supplier', smith.supplier

	def settle_in_cash(self):
		"""
			method to pay the smith the amount owed
		"""
		party_type, party = self.get_smith_party()
		party_account = get_party_account(party_type, party, self.company)
		mode_of_payment_account = get_mode_of_payment_account(self.mode_of_payment, self.company)

		payment_entry = frappe.new_doc('Payment Entry')
		payment_entry.payment_type = 'Pay'
		payment_entry.company = self.company
		payment_entry.posting_date = self.posting_date
		payment_entry.mode_of_payment = self.mode_of_payment
		payment_entry.party_type = party_type
		payment_entry.party = party
		payment_entry.paid_from = mode_of_payment_account
		payment_entry.paid_to = party_account
		payment_entry.paid_amount = self.payable_amount
		payment_entry.received_amount = self.payable_amount
		payment_entry.reference_no = self.reference_no
		payment_entry.reference_date = self.reference_date
		payment_entry.insert(ignore_permissions = True)
		payment_entry.submit()

		self.db_set('payment_entry', payment_entry.name)
		frappe.msgprint(
			msg = _('Payment Entry {0} is created.').format(
				get_link_to_form('Payment Entry', payment_entry.name)
			),
			indicator = 'green',
			alert = 1
		)

	def settle_in_gold(self):
		"""
			method to hand the smith metal in place of money

			The metal leaves the shop for good, so it goes out of the metal ledger as well as
			out of the warehouse. This is not the metal a smith is lent to work on, which the
			Raw Material Bundle books and the buy back closes.
		"""
		if not self.weight:
			frappe.throw(_('The payable amount comes to no weight, so there is nothing to hand over.'))

		stock_entry = frappe.new_doc('Stock Entry')
		stock_entry.stock_entry_type = 'Material Transfer'
		stock_entry.purpose = 'Material Transfer'
		stock_entry.company = self.company
		stock_entry.append('items', {
			'item_code': self.item,
			's_warehouse': self.source_warehouse,
			't_warehouse': frappe.db.get_value('Smith', self.smith, 'warehouse'),
			'qty': self.weight,
			'allow_zero_valuation_rate': 1
		})
		stock_entry.insert(ignore_permissions = True)
		stock_entry.submit()

		self.db_set('stock_entry', stock_entry.name)
		self.create_metal_ledger_entry()

		frappe.msgprint(
			msg = _('Stock Entry {0} is created.').format(
				get_link_to_form('Stock Entry', stock_entry.name)
			),
			indicator = 'green',
			alert = 1
		)

	def create_metal_ledger_entry(self):
		"""
			method to take the metal handed to the smith out of the metal ledger
		"""
		balance_qty = get_metal_balance_qty(
			self.item_type, self.purity, self.stock_uom, self.posting_date, self.posting_time
		)
		frappe.get_doc({
			'doctype': 'Metal Ledger Entry',
			'posting_date': self.posting_date,
			'posting_time': self.posting_time,
			'voucher_type': self.doctype,
			'voucher_no': self.name,
			'company': self.company,
			'party_type': 'Smith',
			'party': self.smith,
			'item_code': self.item,
			'item_name': frappe.db.get_value('Item', self.item, 'item_name'),
			'stock_uom': self.stock_uom,
			'item_type': self.item_type,
			'purity': self.purity,
			'board_rate': self.board_rate,
			'in_qty': 0,
			'out_qty': self.weight,
			'amount': self.payable_amount,
			'balance_qty': balance_qty - flt(self.weight)
		}).insert(ignore_permissions = 1)

		repost_metal_ledger_balance(
			self.item_type, self.purity, self.stock_uom, self.posting_date, self.posting_time
		)
		frappe.msgprint(
			msg = _('Metal Ledger Entry is created.'),
			indicator = 'green',
			alert = 1
		)

	def cancel_payment_entry(self):
		if not self.payment_entry:
			return
		payment_entry = frappe.get_doc('Payment Entry', self.payment_entry)
		if payment_entry.docstatus == 1:
			payment_entry.cancel()

	def cancel_stock_entry(self):
		if not self.stock_entry:
			return
		stock_entry = frappe.get_doc('Stock Entry', self.stock_entry)
		if stock_entry.docstatus == 1:
			stock_entry.cancel()
