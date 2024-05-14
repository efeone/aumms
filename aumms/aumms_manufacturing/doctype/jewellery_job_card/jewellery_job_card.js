// Copyright (c) 2024, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on("Jewellery Job Card", {
  refresh: function(frm){
    create_custom_buttons(frm);
    calculate_total_weight(frm);
    if (frm.doc.docstatus === 1) {
      frm.remove_custom_button('Start');
    }
    frm.set_df_property("duration", "read_only", 1);
    frm.set_df_property("job_time", "read_only",frm.doc.__islocal ? 0 : 1);
  },
  onload: function(frm) {
    frm.get_field('item_details').grid.cannot_add_rows = true;
  },
  validate: function(frm) {
    if (frm.doc.docstatus ==0 && !frm.doc.product_weight) {
      frappe.throw('Product Weight is mandatory.');
      frappe.validated = false;
    }
  }
});

let create_custom_buttons = function(frm){
  if (frm.doc.status == "Open") {
    frm.add_custom_button('Start', () => {
      frm.set_value("status", "Processing");
      updateStartTime(frm);
      frm.save();
      frm.page.set_primary_action(__("Pause"), () => {
        create_custom_buttons(frm);
      }, "btn-primary");
    }).addClass("btn-primary");
  } else if (frm.doc.status == "Processing") {
    frm.add_custom_button(__("Pause"), () => {
      frm.set_value("status", "Hold");
      updateEndTime(frm);
      calculateDuration(frm);
      frm.save();
      create_custom_buttons(frm);
    }).addClass("btn-primary");

    frm.add_custom_button(__("Done"), () => {
      frm.set_value("status", "Complete");
      updateEndTime(frm);
      calculateDuration(frm);
      frm.save();
      create_custom_buttons(frm);
    }).addClass("btn-primary");
  } else if (frm.doc.status == "Hold") {
    frm.add_custom_button('Start', () => {
      frm.set_value("status", "Processing");
      updateStartTime(frm);
      frm.save();
      create_custom_buttons(frm);
    }).addClass("btn-primary");
  }
}


function updateStartTime(frm) {
  const currentTime = frappe.datetime.now_datetime();
  let row = frappe.model.add_child(frm.doc, 'Job Time', 'job_time');
  row.start_time = currentTime;
  frm.refresh_field("job_time");
}

function updateEndTime(frm) {
  const currentTime = frappe.datetime.now_datetime();
  frm.doc.job_time.forEach(function(row) {
    if (row.start_time && !row.end_time) {
      frappe.model.set_value(row.doctype, row.name, 'end_time', currentTime);
    }
  });
}

function calculateDuration(frm) {
  frm.doc.job_time.forEach(function(row) {
    if (row.start_time && row.end_time) {
      const start = moment(row.start_time);
      const end = moment(row.end_time);
      const duration = end.diff(start, 'hours', true);
      frappe.model.set_value(row.doctype, row.name, 'duration', duration);
    }
  });
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

frappe.ui.form.on('Raw Materiel Item',{
  item_details_add : function(frm, cdt, cdn){
    calculate_total_weight(frm);
  },
  item_details_remove : function(frm, cdt, cdn){
    calculate_total_weight(frm);
  }

});

function calculate_total_weight(frm, cdt, cdn){
  let total_weight = 0
  if(frm.doc.item_details){
    frm.doc.item_details.forEach(function(d){
      total_weight += d.weight || 0;
    });
  }
  frm.set_value('weight', total_weight);
};
