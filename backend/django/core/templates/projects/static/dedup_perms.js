/**
 * Deduplicates profiles on permissions on permission update/create pages
 * by disabling select option
 */
function dedupPermProfiles() {
    var selected = [];
    $("select[id$='profile']").each(function() {
        if (this.value != "") selected.push(this.value);
    })
    $("select[id$='profile']").each(function() {
        $(this).find("option:not(:selected)").each(function() {
          // previously unselected option is now selected
          if ($.inArray(this.value, selected) > -1) {
            $(this).attr("disabled", "disabled");
          } else {
            $(this).removeAttr("disabled");
          }
      })
    })
  }

  // Deduplication of profiles on permission page
$("#permSelect").ready(function() {
    dedupPermProfiles();
  })
  
  // New profile-permission row is added
  $("#permSelect").on("DOMNodeInserted", "tr", function() {
    dedupPermProfiles();
  })
  
  // Any other change to permission form
  $("#permSelect").on("change", function() {
    dedupPermProfiles();
  })