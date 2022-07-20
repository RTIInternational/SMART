$("#permSelect").ready(function(){
    $("select[id$='profile']").addClass("searchSelect").select2({
        width: "100%"
    })
})

$("#permSelect").on("DOMNodeInserted", "tr", function() {
    setTimeout( function() {
    $("select[id$='profile']").each(function() {
        if (!$(this).hasClass("searchSelect")) {
        $(this).addClass("searchSelect").select2({
            width: "100%"
        })
        }
    })
    }, 0.1) // Need to wait for all nodes to be inserted
})