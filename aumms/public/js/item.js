frappe.ui.form.on('Item', {
    onload(frm) {
        // show only uoms which is purity uom checked for stock_uom
        set_filter('stock_uom', {is_purity_uom: 1})
        // show only uoms which is purity uom checked for purchase_uom
        set_filter('purchase_uom', {is_purity_uom: 1})
        // show only uoms which is purity uom checked for sales_uom
        set_filter('sales_uom', {is_purity_uom: 1})
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