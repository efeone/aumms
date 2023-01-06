frappe.ui.form.on('Item', {
    onload(frm) {
        // show only uoms which is purity uom checked for stock_uom
        set_filter('stock_uom', {is_purity_uom: 1})
        // show only uoms which is purity uom checked for purchase_uom
        set_filter('purchase_uom', {is_purity_uom: 1})
        // show only uoms which is purity uom checked for sales_uom
        set_filter('sales_uom', {is_purity_uom: 1})
    },
    stock_uom(frm) {
        if (frm.doc.stock_uom) {
            append_purity_uoms(frm)
        }
    }
})

let set_filter = function(field, filters) {
    /*
        function to set filter for a specific field
        args:
            field: field name
            filters: set of filters, (eg: {key:value})
        output: filter applied list for field
    */
    cur_frm.set_query(field, () => {
        return {
            filters: filters
        }
    })
}

let append_purity_uoms = function (frm) {
    /*
        function to append uoms table with all purity uoms
        args:
            frm: current document
    */

    let uoms = []
    let existing_uom = get_existing_uoms(uoms)

    // check uom not in exising uom list and add first uom
    if (!existing_uom.includes(frm.doc.stock_uom)) {
        frm.add_child('uoms', {
            'uom': frm.doc.stock_uom,
            'conversion_factor': 1
        })
        uoms.push(frm.doc.stock_uom)
        frm.refresh_field('uoms');
    }
    // update existing_uom
    existing_uom = get_existing_uoms(uoms)

    // call to get list of purity uoms
    frappe.call('aumms.aumms.doc_events.item.get_purity_uom')
    .then(r => {
        r.message.forEach(uom => {

            // check uom not in exising uom list and add uom
            if (!existing_uom.includes(uom.name)) {
                frm.add_child('uoms', {
                    'uom': uom.name
                })
            }
		});
        frm.refresh_field('uoms');
    })
}

let get_existing_uoms = function (uoms) {

    // function to get all existing uom in the doc as list
    if (cur_frm.doc.uoms) {
        cur_frm.doc.uoms.forEach( uom => {
            uoms.push(uom.uom)
        });
    }
    return uoms;

}