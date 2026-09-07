frappe.ui.form.on('Delivery Note', {
  refresh(frm) {
    show_metal_ledger(frm)
  }
})

let show_metal_ledger = function(frm) {
  //Sits beside the Stock Ledger button, so the metal a voucher moved reads off the note.
  //The metal leaves the shop here when the invoice did not update the stock itself.
  //A cancelled note asks for its cancelled entries, which the report otherwise hides, or
  //the button would open an empty report.
  if (frm.doc.docstatus > 0 && frm.doc.keep_metal_ledger) {
    frm.add_custom_button(__('Metal Ledger'), function() {
      frappe.route_options = {
        voucher_no: frm.doc.name,
        from_date: frm.doc.posting_date,
        to_date: moment(frm.doc.modified).format('YYYY-MM-DD'),
        company: frm.doc.company,
        show_cancelled_entries: frm.doc.docstatus === 2
      }
      frappe.set_route('query-report', 'Metal Ledger')
    }, __('View'))
  }
}
