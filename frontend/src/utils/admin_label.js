/* global PROJECT_PK:false */

/*
 *  Make ajax call to `label_distribution` route.  This will fetch data to
 *  populate the discrete multi bar chart and show the label distribution
 *  per user.
 */
$.ajax({
    method: "GET",
    url: '/api/label_distribution/' + PROJECT_PK + '/',
    success: function (response) {
        nv.addGraph(function() {
            const chart = nv.models.multiBarChart()
                .color(["#66c2a5", "#fc8d62", "#8da0cb", "#e78ac3", "#a6d854", "#ffd92f", "#e5c494", "#b3b3b3"])
                .duration(300)
                .margin({ bottom: 70, left: 70 })
                .groupSpacing(0.1)
            ;
            chart.xAxis
                .axisLabel("User")
                .axisLabelDistance(15)
                .showMaxMin(false)
            ;
            chart.yAxis
                .axisLabel("Number of Data Annotated")
                .axisLabelDistance(-5)
                .tickFormat(d3.format(',.01f'))
            ;
            chart.showControls(false);
            chart.showLegend(false);
            chart.noData("Insufficient labeled data -- please code more documents");
            d3.select('#distribution_chart svg')
                .datum(response)
                .call(chart);
            nv.utils.windowResize(chart.update);
            return chart;
        });
    },
    error: function (error) {
        console.log(error);
    }
});


/*
 *  Make ajax call to `label_timing` route.  This will fetch data to populate
 *  the boxplot/candlestick chart and show how long it takes each user to
 *  annotate data.
 */
$.ajax({
    method: 'GET',
    url: '/api/label_timing/' + PROJECT_PK + '/',
    success: function (response) {
        nv.addGraph(function() {
            let chart = nv.models.boxPlotChart()
                .x(function (d) {
                    return d.label;
                })
                .staggerLabels(true)
                .maxBoxWidth(75) // prevent boxes from being incredibly wide
                .yDomain([0, response.yDomain])
            ;
            chart.xAxis
                .axisLabel("User")
                .axisLabelDistance(15)
                .showMaxMin(false)
            ;
            chart.yAxis
                .axisLabel("Time to Label (s)")
                .axisLabelDistance(-5)
                .tickFormat(d3.format(','))
            ;
            chart.noData("Insufficient labeled data -- please code more documents");
            d3.select('#timer_chart svg')
                .datum(response.data)
                .call(chart);
            nv.utils.windowResize(chart.update);
            return chart;
        });
    },
    error: function (error) {
        console.log(error);
    }
});

$(document).ready(function() {
    /*
     *  Activate DataTable script to create the labeled data DataTable
     */
    $('#labeled_data_table').DataTable({
        "ajax": '/api/data_coded_table/' + PROJECT_PK + '/',
        "columns": [
            { "data": "Text", "width": "70%" },
            { "data": "Label", "searchable": false, "width": "15%" },
            { "data": "Coder", "searchable": false, "width": "15%" }
        ],
        "oLanguage": {
            "sSearch": "Filter Text: ",
            "sEmptyTable": "Insufficient labeled data -- please code more documents"
        },
        "initComplete": function () {
            let $this = $(this);
            $this.css({ 'table-layout':'fixed' });
            $this.find('tr td:first-child').addClass('showData');
            window.dispatchEvent(new Event('resize'));
        },
        "rowCallback": function (row) {
            $('td:nth-child(1)', row).addClass('showData');
        }
    });
});
