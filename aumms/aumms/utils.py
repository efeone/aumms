import frappe
from frappe import _
from frappe.utils import *

@frappe.whitelist()
def get_board_rate(item_type, purity, stock_uom, date, time=None):
    ''' Method to get Board Rate '''

    # add filters to get board rate
    if time:
        filters = { 'docstatus': '1', 'item_type': item_type, 'purity': purity, 'date': getdate(date), 'time': ['<=', time] }
    else:
        filters = { 'docstatus': '1', 'item_type': item_type, 'purity': purity, 'date': getdate(date) }

    if frappe.db.exists('Board Rate', filters):
        # get board rate and board rate uom (br_uom)
        board_rate, br_uom = frappe.db.get_value('Board Rate', filters, ['board_rate', 'uom'])
        # return board rate if board rate uom is same as stock uom
        if br_uom == stock_uom:
            return board_rate
        # else multiply the board rate with conversion factor
        else:
            if stock_uom == "Nos" or br_uom == 'Gram' or br_uom == 'Nos':
                return board_rate
            # get conversion factor value using stock_uom as from_uom and br_uom as to_uom
            conversion_factor = get_conversion_factor(stock_uom, br_uom)
            if conversion_factor:
                board_rate *= conversion_factor
                return board_rate
            else:
                # message to user about set conversion factor value
                frappe.throw(
                    _('Please set Conversion Factor for {0} to {1}'.format(stock_uom, br_uom))
                )
    else:
        # message to user about set Today's Board Rate value
        frappe.throw(
            _('No Board Rate found for  <B>{0}</B> <B>{1}</B> on <B>{2}</B>'.format(purity, item_type, date))
        )

@frappe.whitelist()
def get_conversion_factor(from_uom, to_uom):
    """
        method to get conversion factor value using from uom and to uom
        output:
            return conversion factor value if exists else None
    """
    filters = {'from_uom': from_uom, 'to_uom': to_uom}
    return frappe.db.get_value('UOM Conversion Factor', filters, 'value')

def get_metal_ledger_filters(item_type, purity, stock_uom):
    """
        method to get the filters that identify one metal ledger series
        args:
            item_type: item type link
            purity: purity link
            stock_uom: the weight uom the series is held in
        output: filters dict matching the live entries of that series
    """
    return {
        'item_type': item_type,
        'purity': purity,
        'stock_uom': stock_uom,
        'is_cancelled': 0
    }

def get_metal_qty(aumms_item_doc, item):
    """
        method to get the metal a row moves, and the uom that weight is held in
        args:
            aumms_item_doc: object of the AuMMS Item document
            item: row of the purchase receipt or sales invoice items table
        output: tuple of the weight moved and the weight uom it is measured in

        The row quantity counts pieces, the stock uom being Nos for a finished item, so it
        cannot go on a metal ledger as it stands. The gold weight held on the Item master is
        the metal in one piece, stone excluded, so multiplying it by the stock quantity gives
        the metal that actually moved. An item already stocked by weight needs no conversion.
    """
    weight_uom = aumms_item_doc.weight_uom or item.get('weight_uom')

    if weight_uom and aumms_item_doc.stock_uom == weight_uom:
        return flt(item.stock_qty), weight_uom

    weight_per_unit = flt(aumms_item_doc.gold_weight) or flt(aumms_item_doc.weight_per_unit)
    if not weight_per_unit or not weight_uom:
        # message to user about set Gold Weight and Weight UOM on the item
        frappe.throw(
            _('Set Gold Weight and Weight UOM on Item {0} to keep a Metal Ledger for it.'.format(aumms_item_doc.name))
        )

    return weight_per_unit * flt(item.stock_qty), weight_uom

def get_metal_balance_qty(item_type, purity, stock_uom, posting_date=None, posting_time=None):
    """
        method to get the balance a metal ledger series carries into a posting datetime
        args:
            item_type: item type link
            purity: purity link
            stock_uom: the weight uom the series is held in
            posting_date: date the balance is read as at, the whole series if not given
            posting_time: time the balance is read as at
        output: balance qty of the latest live entry standing before that moment, else 0

        Read on posting datetime rather than on modified time, so a back dated entry opens
        from the balance that stood when it is posted and not from a later one.
    """
    conditions = ''
    values = { 'item_type': item_type, 'purity': purity, 'stock_uom': stock_uom }

    if posting_date:
        conditions = ' AND TIMESTAMP(posting_date, posting_time) < TIMESTAMP(%(posting_date)s, %(posting_time)s)'
        values['posting_date'] = posting_date
        values['posting_time'] = posting_time or '00:00:00'

    balance_qty = frappe.db.sql("""
        SELECT
            balance_qty
        FROM
            `tabMetal Ledger Entry`
        WHERE
            item_type = %(item_type)s AND purity = %(purity)s
            AND stock_uom = %(stock_uom)s AND is_cancelled = 0 {conditions}
        ORDER BY
            posting_date DESC, posting_time DESC, creation DESC
        LIMIT 1
    """.format(conditions = conditions), values)

    return flt(balance_qty[0][0]) if balance_qty else 0

def repost_metal_ledger_balance(item_type, purity, stock_uom, posting_date=None, posting_time=None):
    """
        method to rewrite the running balance of a metal ledger series
        args:
            item_type: item type link
            purity: purity link
            stock_uom: the weight uom the series is held in
            posting_date: date to repost from, the whole series if not given
            posting_time: time to repost from

        balance_qty is stored on each entry, so an entry added or cancelled part way through
        a series leaves every later balance wrong. Only the entries standing at or after the
        voucher are walked, the ones before it being untouched by the change.
    """
    balance_qty = get_metal_balance_qty(item_type, purity, stock_uom, posting_date, posting_time)

    conditions = ''
    values = { 'item_type': item_type, 'purity': purity, 'stock_uom': stock_uom }

    if posting_date:
        conditions = ' AND TIMESTAMP(posting_date, posting_time) >= TIMESTAMP(%(posting_date)s, %(posting_time)s)'
        values['posting_date'] = posting_date
        values['posting_time'] = posting_time or '00:00:00'

    entries = frappe.db.sql("""
        SELECT
            name, in_qty, out_qty
        FROM
            `tabMetal Ledger Entry`
        WHERE
            item_type = %(item_type)s AND purity = %(purity)s
            AND stock_uom = %(stock_uom)s AND is_cancelled = 0 {conditions}
        ORDER BY
            posting_date ASC, posting_time ASC, creation ASC
    """.format(conditions = conditions), values, as_dict = 1)

    for entry in entries:
        balance_qty += flt(entry.in_qty) - flt(entry.out_qty)
        frappe.db.set_value(
            'Metal Ledger Entry', entry.name, 'balance_qty', balance_qty, update_modified = False
        )

@frappe.whitelist()
def create_metal_ledger_entries(doc, method=None):
    """
        method to create metal ledger entries
        args:
            doc: object of purchase Receipt doctype and Sales Invoice doctype
            method: on submit of purchase reciept and Sales Invoice
        output:
            new metal ledger entry doc
    """

    # get default company
    company = frappe.defaults.get_defaults().company

    # set dict of fields for metal ledger entry
    fields = {
        'doctype': 'Metal Ledger Entry',
        'posting_date': doc.posting_date,
        'posting_time': doc.posting_time,
        'voucher_type': doc.doctype,
        'voucher_no': doc.name,
        'company': company,
        # 'party_link': doc.party_link
    }

    # set party type and party in fields if doctype is Purchase Receipt
    if doc.doctype == 'Purchase Receipt':
        fields['party_type'] = 'Supplier'
        fields['party'] = doc.supplier

    # set party type and party in fields if doctype is Sales Invoice
    if doc.doctype == 'Sales Invoice':
        fields['party_type'] = 'Customer'
        fields['party'] = doc.customer

    # check items is keep_metal_ledger
    if doc.keep_metal_ledger:
        # declare ledger_created as false
        ledger_created = 0
        # series touched by this voucher, reposted once each after the entries are in
        metal_ledger_series = set()
        for item in doc.items:
            
                aumms_item_doc = frappe.get_doc("AuMMS Item", item.item_code)

                # get the metal moved and the weight uom it is measured in, off the Item master
                metal_qty, weight_uom = get_metal_qty(aumms_item_doc, item)

                # set item details in fields
                fields['item_code'] = item.item_code
                fields['item_name'] = item.item_name
                fields['stock_uom'] = weight_uom
                fields['purity'] = aumms_item_doc.purity
                fields['purity_percentage'] = aumms_item_doc.purity_percentage
                fields['board_rate'] = item.board_rate
                fields['batch_no'] = item.batch_no
                fields['item_type'] = aumms_item_doc.item_type
                # get balance qty of the item for this party
                balance_qty = get_metal_balance_qty(
                    aumms_item_doc.item_type, aumms_item_doc.purity, weight_uom,
                    doc.posting_date, doc.posting_time
                )
                metal_ledger_series.add((aumms_item_doc.item_type, aumms_item_doc.purity, weight_uom))

                if doc.doctype == 'Purchase Receipt':
                    # update balance_qty
                    fields['in_qty'] = metal_qty
                    fields['out_qty'] = 0
                    fields['outgoing_rate'] = item.rate
                    fields['balance_qty'] = balance_qty + metal_qty
                    fields['amount'] = -item.amount

                if doc.doctype == 'Sales Invoice':
                    # update balance_qty
                    fields['incoming_rate'] = item.rate
                    fields['in_qty'] = 0
                    fields['out_qty'] = metal_qty
                    fields['balance_qty'] = balance_qty - metal_qty
                    fields['amount'] = item.amount

                # create metal ledger entry doc with fields
                frappe.get_doc(fields).insert(ignore_permissions = 1)
                ledger_created = 1

        # a back dated voucher lands before entries that are already posted, so their balance
        # is rewritten too. A voucher posted last of all walks only its own rows.
        for item_type, purity, stock_uom in metal_ledger_series:
            repost_metal_ledger_balance(
                item_type, purity, stock_uom, doc.posting_date, doc.posting_time
            )

        # alert message if metal ledger is created
        if ledger_created:
            frappe.msgprint(
                msg = _(
                    'Metal Ledger Entry is created.'
                ),
                indicator="green",
                alert = 1
            )

@frappe.whitelist()
def cancel_metal_ledger_entries(doc, method=None):
    """
        method to cancel metal ledger entries of this voucher
        args:
            doc: object of purchase receipt and Sales Invoice
            method: on cancel of purchase receipt and Sales Invoice

        The entries are flagged rather than reversed, the way the Stock Ledger cancels its
        own, so the metal returns to the balance as soon as the flag is set. The balance of
        the entries left behind is then rewritten, or the next entry of the series would open
        from a figure that still counts the cancelled one.
    """
    # get all live Metal Ledger Entry linked with this doctype
    ml_entries = frappe.get_all('Metal Ledger Entry',
        filters = {
            'voucher_type': doc.doctype,
            'voucher_no': doc.name,
            'is_cancelled': 0
        },
        fields = ['name', 'item_type', 'purity', 'stock_uom']
    )

    for ml in ml_entries:
        # get doc of metal ledger entry
        ml_doc = frappe.get_doc('Metal Ledger Entry', ml.name)
        # change is_cancelled value from 0 to 1
        ml_doc.is_cancelled = 1
        # ignoring this doctype from linked metal ledger doc
        ml_doc.ignore_linked_doctypes = (doc.doctype,)
        # ignoring the links with this doctype
        ml_doc.flags.ignore_links = 1
        ml_doc.save(ignore_permissions = 1)

    # repost once per series, so a voucher holding several rows of one series is walked once
    for item_type, purity, stock_uom in {(ml.item_type, ml.purity, ml.stock_uom) for ml in ml_entries}:
        repost_metal_ledger_balance(
            item_type, purity, stock_uom, doc.posting_date, doc.posting_time
        )

    # alert message if metal ledger is cancelled
    if ml_entries:
        frappe.msgprint(
            msg = _(
                'Metal Ledger Entries are cancelled.'
            ),
            indicator = "orange",
            alert = 1
        )

@frappe.whitelist()
def validate_party_for_metal_transaction(doc, method=None):
    """
        method to validate party link if the transaction is metal transaction
        args:
            doc: object instance of the sales invoice/ purchase receipt document
    """
    # get_party_link_if_exist if doctype is Purchase Receipt
    if doc.doctype == 'Purchase Receipt':
        if doc.keep_metal_ledger:
            # check supplier is linked
            party_link = get_party_link_if_exist('Supplier', doc.supplier)
            doc.party_link = party_link

    # get_party_link_if_exist if doctype is Sales Invoice
    if doc.doctype == 'Sales Invoice':
        if doc.keep_metal_ledger:
            # check customer is linked
            party_link =  get_party_link_if_exist('Customer', doc.customer)
            doc.party_link = party_link

@frappe.whitelist()
def get_party_link_if_exist(party_type, party):
    """
        function to check party link exist for party and throw a message if not exists
        args:
            party_type : "Customer" or "Supplier"
            party : name of customer/ supplier
        output:
            party link or message to the user if the party is not linked
    """
    query = """
        SELECT
            name
        FROM
            `tabParty Link`
        WHERE
            (primary_role = %(party_type)s AND primary_party = %(party)s ) OR (secondary_role = %(party_type)s AND secondary_party = %(party)s )
    """
    party_link = frappe.db.sql(query.format(), { 'party_type':party_type, 'party':party }, as_dict = 1)

    if not party_link:
        # message to the user if party link is not set
        frappe.throw( _("{0} doesn't have a common party account!".format(party)))
    else:
        return party_link[0].name

@frappe.whitelist()
def increase_precision():
    ''' Method to increase precision on System Settings after migrate '''
    if cint(frappe.db.get_single_value("System Settings", "setup_complete") or 0):
        system_settings_doc = frappe.get_doc('System Settings')
        system_settings_doc.float_precision = 6
        system_settings_doc.save()
        frappe.db.commit()

@frappe.whitelist()
def get_advances_payments_against_so(sales_order):
    ''' Method to get advance payments against SO based on date and Board Rate '''
    query = '''
        SELECT
            pe.name as payment_entry,
            pe.posting_date as posting_date,
            per.allocated_amount as amount
        FROM
            `tabPayment Entry` as pe,
            `tabPayment Entry Reference` as per
        WHERE
            pe.name = per.parent AND
            per.reference_doctype = 'Sales Order' AND
            per.reference_name = '{0}'
        ORDER BY
            pe.posting_date asc
    '''.format(sales_order)
    advances = frappe.db.sql(query, as_dict = 1)
    return advances

@frappe.whitelist()
def get_advances_payments_against_so_in_gold(sales_order, item_type, purity, stock_uom):
    ''' Method to get cadvance payments against SO in terms of gold '''
    advances = get_advances_payments_against_so(sales_order)
    for advance in advances:
        advance['item_type'] = item_type
        advance['purity'] = purity
        advance['stock_uom'] = stock_uom
        advance['board_rate'] = 0
        advance['qty_obtained'] = 0
        board_rate = get_board_rate(item_type, purity, stock_uom, advance.get('posting_date'))
        if board_rate:
            advance['board_rate'] = board_rate
            if advance.get('amount'):
                advance['qty_obtained'] = float(advance.get('amount'))/float(board_rate)
    return advances

# Notification Function
@frappe.whitelist()
def create_notification_log(doctype, docname, recipient, subject, content=None, type=None):
    """method is used to create notification log
    args:
        doc: document object
        recipient: notification receiving user
        subject: subject of notification log
        type: type of the notification log"""
    notification_log = frappe.new_doc("Notification Log")
    notification_log.type = "Mention"
    if type:
        notification_log.type = type
    notification_log.document_type = doctype
    notification_log.document_name = docname
    notification_log.for_user = recipient
    notification_log.subject = subject
    if content:
        notification_log.email_content = content
    notification_log.save(ignore_permissions=True)

@frappe.whitelist()
def rejection_action(doctype,doc,comment):
    doc = frappe.get_doc(doctype,doc)
    if comment:
        doc.add_comment('Comment', comment)
        return True
