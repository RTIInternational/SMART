/* global PROJECT_PK:false, PROJECT_CLASSIFIER:false, PROJECT_LEARNING_METHOD:false */

/*
 *  Make ajax call to `model_metrics` route.  This will fetch data to populate
 *  the line chart and show how well the model is training over time.
 */
if (PROJECT_CLASSIFIER !== 'None') {
    $.ajax({
        method: 'GET',
        url: '/api/model_metrics/' + PROJECT_PK + '/?metric=accuracy',
        success: function (response) {
            let chart;
            nv.addGraph(function() {
                chart = nv.models.lineChart()
                    .options({
                        duration: 300,
                        useInteractiveGuideline: true,
                        forceY: [0, 1]
                    })
                ;
                chart.xAxis
                    .axisLabel("Run ID")
                ;

                chart.yAxis
                    .axisLabel('Metric')
                    .tickFormat(function(d) {
                        return d3.format(',.2f')(d);
                    })
                ;
                chart.noData("Insufficient training data -- please code more documents");
                d3.select('#metric_chart svg')
                    .datum(response)
                    .call(chart);
                nv.utils.windowResize(chart.update);
                return chart;
            });
            $('#metric_select').change(function () {
                $.ajax({
                    method: 'GET',
                    url: '/api/model_metrics/' + PROJECT_PK + '/?metric=' + $(this).val(),
                    success: function (response) {
                        d3.select('#metric_chart svg')
                            .datum(response)
                            .transition()
                            .duration(300)
                            .call(chart);
                        nv.utils.windowResize(chart.update);
                    },
                    error: function (error) {
                        console.log(error);
                    }
                });
                let choice = $(this).val();
                let children = $("#model_metrics").children();
                if (choice === "accuracy") {
                    $("#model_metrics").text("Model Metrics: Accuracy ");
                    $("#model_metrics").append(children);
                    $("#model_metric_icon").attr("title", "The percent guessed correctly by the model.");
                } else if (choice === "f1") {
                    $("#model_metrics").text("Model Metrics: F1 Score ");
                    $("#model_metrics").append(children);
                    $("#model_metric_icon").attr("title", "A common model evaluation "
                      + "metric with a similar interpretation to accuracy but penalizes "
                      + "for poor precision or recall. This is an important consideration"
                      + " when predicting rare classes. Formula: 2*((Precision * Recall)/(Precision + Recall))");
                } else if (choice === "precision") {
                    $("#model_metrics").text("Model Metrics: Precision ");
                    $("#model_metrics").append(children);
                    $("#model_metric_icon").attr("title", "Indicates how precise the"
                      + " active learning model is at correctly predicting the category"
                      + " in the test set. Formula:  True Positives/(True Positives + False Positives)");
                } else {
                    $("#model_metrics").text("Model Metrics: Recall ");
                    $("#model_metrics").append(children);
                    $("#model_metric_icon").attr("title", "Indicates how comprehensive"
                      + " the active learning model is at identifying documents of a "
                      + "particular category in the test set.  Formula:  "
                      + "True Positives/(True Positives + False Negatives)");
                }
                $(function () {
                    $('[data-toggle="tooltip"]').tooltip();
                });
            });

        },
        error: function (error) {
            console.log(error);
        }
    });
}


$(document).ready(function() {
    /*
     *  Activate DataTable script to create the predicted data DataTable
     */
    if (PROJECT_CLASSIFIER !== 'None' && PROJECT_LEARNING_METHOD !== 'random') {
        $('#predicted_data_table').DataTable({
            "ajax": '/api/data_predicted_table/' + PROJECT_PK + '/',
            "columns": [
                { "data": "Text", "width": "70%" },
                { "data": "Probability",
                    "searchable": false,
                    "width": "15%",
                    "render": function (data) {
                        return d3.format('.2%')(data);
                    },
                },
                { "data": "Label", "searchable": false, "width": "15%" }
            ],
            "oLanguage": {
                "sSearch": "Filter Text: ",
                "sEmptyTable": "Insufficient training data -- please code more documents"
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
    }
});
