/* global PROJECT_PK:false, PROJECT_PERCENTAGE_IRR:false */

function drawHeatmap(response) {
    let coders = response["coders"];
    let labels = response["labels"];
    let coder1 = $('#coder1_select').val();
    let coder2 = $('#coder2_select').val();
    let comb1 = coder1.toString() + "_" + coder2.toString();
    let comb2 = coder2.toString() + "_" + coder1.toString();
    let data;
    if (comb1 in response['data']) {
        data = response['data'][comb1];
    } else {
        data = response['data'][comb2];
    }

    let all_zero = true;
    //don't draw the heatmap if there is no data
    let most_data = 0;
    try {
        for (let i = 0; i < data.length; i++) {
            if (data[i]["count"] > most_data) {
                most_data = data[i]["count"];
            }
            if (data[i]["count"] > 0) {
                all_zero = false;
            }
        }
    } catch (error) {
        all_zero = true;
    }

    let coder1_name = "";
    let coder2_name = "";
    //get the coder names to use for the axis labels
    coders.forEach(function(coder){
        if (coder.pk.toString() === coder1) {
            coder1_name = coder.name;
        }
        if (coder.pk.toString() === coder2) {
            coder2_name = coder.name;
        }

    });

    //Code adapted from blocks example:
    //http://bl.ocks.org/tjdecke/5558084
    let margin = { top: 100, right: 100, bottom: 200, left: 100 };
    let width, height;
    if (labels.length > 10) {
        width = labels.length * 50;
        height = labels.length * 50;
    } else {
        width = 500;
        height = labels.length * 50;
    }

    let colors = ["#ffffff", "#deebf7", "#c6dbef", "#9ecae1", "#6baed6", "#4292c6", "#2171b5", "#08519c", "#08306b"];
    let buckets;
    if (most_data >= 9) {
        buckets = 9;
    } else {
        buckets = most_data + 1;
        colors = colors.slice(0, buckets);
    }

    let gridSize = 50,
        legendElementWidth = 30;

    //delete the old chart
    d3.select('#heatmap').remove();

    if (!all_zero) {
    //append the new svg to put everything in
        let svg = d3.select("#heatmap_chart").append("svg")
            .attr("id", "heatmap")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        //add the y axis labels
        svg.selectAll(".vertLabel")
            .data(labels)
            .enter()
            .append("text")
            .text(function (d) {
                return d.slice(0, 5);
            })
            .attr("x", 0)
            .attr("y", function (d, i) {
                return i * gridSize;
            })
            .style("text-anchor", "end")
            .attr("transform", "translate(-6," + gridSize / 1.5 + ")")
            .attr("class", function (d, i) {
                return ((i >= 0 && i <= 4) ? "vertLabel mono axis axis-workweek" : "vertLabel mono axis");
            });

        //add the x axis labels
        svg.selectAll(".horzLabel")
            .data(labels)
            .enter()
            .append("text")
            .text(function(d) {
                return d.slice(0, 5);
            })
            .attr("x", function(d, i) {
                return i * gridSize;
            })
            .attr("y", 0)
            .style("text-anchor", "middle")
            .attr("transform", "translate(" + gridSize / 2 + ", -6)")
            .attr("class", function(d, i) {
                return ((i >= 7 && i <= 16) ? "horzLabel mono axis axis-worktime" : "horzLabel mono axis");
            });

        let colorScale = d3.scale.quantile()
            .domain([0, most_data + 1])
            .range(colors);

        let cards = svg.selectAll(".label2")
            .data(data, function(d) {
                return d.label1 + ':' + d.label2;
            });
        cards.append("title");

        cards.enter().append("rect")
            .attr("x", function(d) {
                return (labels.indexOf(d.label1) * gridSize);
            })
            .attr("y", function(d) {
                return (labels.indexOf(d.label2) * gridSize);
            })
            .attr("rx", 4)
            .attr("ry", 4)
            .attr("class", "hour bordered")
            .attr("width", gridSize)
            .attr("height", gridSize)
            .style("fill", function(d) {
                //Manually calculate the colors since the quantiles
                //can have roundoff errors (ex: 1.00000001)
                let quantiles = [0].concat(colorScale.quantiles());
                for (let i = 0; i < quantiles.length; i++) {
                    if (d.count <= Math.round(quantiles[i])) {
                        return colors[i];
                    }
                }
                return "#000000";
            });

        cards.select("title").text(function(d) {
            return d.count;
        });

        //Axis code found at https://bl.ocks.org/d3noob/23e42c8f67210ac6c678db2cd07a747e
        // text label for the x axis
        svg.append("text")
            .attr("transform",
                "translate(" + (width / 5) + " ," +
                             (-50) + ")")
            .style("text-anchor", "middle")
            .text(coder1_name);
        // text label for the y axis
        svg.append("text")
            .attr("transform", "rotate(-90)")
            .attr("y", -70)
            .attr("x", 0 - (height / 5))
            .attr("dy", "1em")
            .style("text-anchor", "middle")
            .text(coder2_name);

        cards.exit().remove();

        let legend = svg.selectAll(".legend")
            .data([0].concat(colorScale.quantiles()), function(d) {
                return d;
            });

        legend.enter().append("g")
            .attr("class", "legend");

        legend.append("rect")
            .attr("x", function(d, i) {
                return legendElementWidth * i;
            })
            .attr("y", height + margin.top)
            .attr("width", legendElementWidth)
            .attr("height", gridSize / 2)
            .style("fill", function(d, i) {
                return colors[i];
            });

        legend.append("text")
            .attr("class", "mono")
            .text(function(d) {
                return "≥ " + Math.round(d);
            })
            .attr("x", function(d, i) {
                return legendElementWidth * i;
            })
            .attr("y", height + gridSize + margin.top);

        legend.exit().remove();
    }

}

if (PROJECT_PERCENTAGE_IRR > 0) {
    /*
     *  Make ajax call to `get_irr_metrics` route.  This will fetch the
     *  common irr metrics to be displayed for the user
     */
    $.ajax({
        method: "GET",
        url: '/api/get_irr_metrics/' + PROJECT_PK + '/',
        success: function (response) {
            $('#kappa').text(response.kappa.toString());
            $('#percent_agree').text(response['percent agreement'].toString());
        },
        error: function (error) {
            console.log(error);
        }
    });


    /*
     *  Make ajax call to get the data for the heatmap.
     */
    $.ajax({
        method: "GET",
        url: '/api/heat_map_data/' + PROJECT_PK + '/',
        success: function (response) {
            let coders = response['coders'];

            if (coders.length >= 2) {
                coders.map(function(coder){
                    $('#coder1_select').append('<option value="' + coder.pk.toString() + '">' + coder.name + '</option>');
                    $('#coder2_select').append('<option value="' + coder.pk.toString() + '">' + coder.name + '</option>');
                });
                drawHeatmap(response);
            }
        },
        error: function (error) {
            console.log(error);
        }
    });

    $('#coder1_select').change(function () {
        $.ajax({
            method: 'GET',
            url: '/api/heat_map_data/' + PROJECT_PK + '/',
            success: function (response) {
                drawHeatmap(response);
            },
            error: function (error) {
                console.log(error);
            }
        });
    });

    $('#coder2_select').change(function () {
        $.ajax({
            method: 'GET',
            url: '/api/heat_map_data/' + PROJECT_PK + '/',
            success: function (response) {
                drawHeatmap(response);
            },
            error: function (error) {
                console.log(error);
            }
        });
    });

    $(document).ready(function() {
        /*
         *  Activate DataTable script to create the labeled data DataTable
         */
        $('#pairwise_perc_agreement_table').DataTable({
            "ajax": '/api/perc_agree_table/' + PROJECT_PK + '/',
            "columns": [
                { "data": "First Coder", "searchable": true },
                { "data": "Second Coder", "searchable": false },
                { "data": "Percent Agreement", "searchable": false }
            ],
            "oLanguage": {
                "sSearch": "Filter First Coder: ",
                "sEmptyTable": "No irr data processed"
            },
            "initComplete": function () {
                let $this = $(this);
                $this.css({ 'table-layout':'fixed' });
            }
        });
    });
}
