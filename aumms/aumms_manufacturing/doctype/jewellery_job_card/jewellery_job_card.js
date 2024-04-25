// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on("Jewellery Job Card", {
  refresh: function(frm){
    create_custom_buttons(frm);
  }
});

let create_custom_buttons = function(frm){
  if (frm.doc.status == "Open") {
    frm.add_custom_button('Start', () => {
      frm.set_value("status", "Processing");
      frm.save();
      frm.page.set_primary_action(__("Pause"), () => {
        create_custom_buttons(frm);
      }, "btn-primary");
    }).addClass("btn-primary");
  } else if (frm.doc.status == "Processing") {
    frm.add_custom_button(__("Pause"), () => {
      frm.set_value("status", "Hold");
      frm.save();
      create_custom_buttons(frm);
    }).addClass("btn-primary");
  } else if (frm.doc.status == "Hold") {
    frm.add_custom_button('Start', () => {
      frm.set_value("status", "Processing");
      frm.save();
      create_custom_buttons(frm);
    }).addClass("btn-primary");

    frm.add_custom_button(__("Done"), () => {
      frm.set_value("status", "Complete");
      frm.save();
      create_custom_buttons(frm);
    }).addClass("btn-primary");
  }
}

frappe.ui.form.on("Job Time", {
  duration : function(frm, cdt, cdn){
    let total_duration = 0
    if(frm.doc.job_time){
      frm.doc.job_time.forEach(function(d){
        if(d.duration){
          total_duration += d.duration || 0
        }
      });
    }
    frm.set_value('duration',total_duration);
  },
  job_time_remove : function(frm, cdt, cdn){
    let total_duration = 0
    if(frm.doc.job_time){
      frm.doc.job_time.forEach(function(d){
        if(d.duration){
          total_duration += d.duration || 0
        }
      });
    }
    frm.set_value('duration',total_duration);
  }
});
