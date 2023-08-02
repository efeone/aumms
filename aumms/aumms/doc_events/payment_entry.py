import frappe

def payment_entry_on_submit(doc, method):
    ''' Method to trigger on_submit of payment entry '''
    if doc.references:
        jewellery_invoice = False
        for row in doc.references:
            if row.reference_name:
                if row.reference_doctype == 'Sales Invoice':
                    jewellery_invoice = get_jewellery_invoice(row.reference_doctype, row.reference_name, 'sales_invoice')
                if row.reference_doctype == 'Sales Order':
                    jewellery_invoice = get_jewellery_invoice(row.reference_doctype, row.reference_name, 'sales_order')
                if jewellery_invoice:
                    #Update Status if reference doctype is Sales Order or Sales Invoice
                    update_jewellery_invoice(jewellery_invoice)

def get_jewellery_invoice(reference_doctype, reference_name, reference_field):
    ''' Method to get Jewellery Invoice with reference mentioned in Payment Entry '''
    invoice_id = False
    if frappe.db.exists('Jewellery Invoice', { reference_field:reference_name }):
        invoice_id = frappe.db.get_value('Jewellery Invoice', { reference_field:reference_name })
    return invoice_id

def update_jewellery_invoice(invoice_id):
    ''' Method to set Jewellery Invoice status based on Payment Entry '''
    jewellery_invoice_status = ['Unpaid', 'Paid', 'Partly Paid', 'Overdue']
    if frappe.db.exists('Jewellery Invoice', invoice_id):
        sales_order, sales_invoice = frappe.db.get_value('Jewellery Invoice', invoice_id, ['sales_order', 'sales_invoice'])
        total = frappe.db.get_value("Jewellery Invoice", invoice_id, 'rounded_total')
        if sales_invoice:
            #Checking status and amount for Sales Invoice
            outstanding_amount = frappe.db.get_value('Sales Invoice', sales_invoice, 'outstanding_amount')
            status = frappe.db.get_value('Sales Invoice', sales_invoice, 'status')
            frappe.db.set_value("Jewellery Invoice", invoice_id, 'outstanding_amount', float(outstanding_amount))
            frappe.db.set_value("Jewellery Invoice", invoice_id, 'paid_amount', float(total) - float(outstanding_amount))
            if status in jewellery_invoice_status:
                frappe.db.set_value("Jewellery Invoice", invoice_id, 'status', status)
        elif sales_order:
            #Checking status and amount for Sales Order
            advance_paid = frappe.db.get_value('Sales Order', sales_order, 'advance_paid')
            outstanding_amount = float(total) - float(advance_paid)
            frappe.db.set_value("Jewellery Invoice", invoice_id, 'paid_amount', float(advance_paid))
            frappe.db.set_value("Jewellery Invoice", invoice_id, 'outstanding_amount', float(outstanding_amount))
            if outstanding_amount>0:
                if advance_paid>0:
                    frappe.db.set_value("Jewellery Invoice", invoice_id, 'status', 'Partly Paid')
                else:
                    frappe.db.set_value("Jewellery Invoice", invoice_id, 'status', 'Unpaid')
            else:
                frappe.db.set_value("Jewellery Invoice", invoice_id, 'status', 'Paid')
        frappe.db.commit()
