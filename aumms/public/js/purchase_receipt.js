frappe.ui.form.on('Purchase Receipt', {
  refresh (frm) {
    if ([1, 2].includes(frm.doc.docstatus)) {

      // Custom button Metal Ledger in View
      frm.add_custom_button('Metal Ledger', () => {
        // route to Metal Ledger Report with filter of this voucher no
        frappe.set_route('query-report', 'Metal Ledger', { 'voucher_no': frm.doc.name });
      }, 'View');

    }
  }

});