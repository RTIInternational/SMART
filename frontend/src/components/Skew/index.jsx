import React from "react";
import PropTypes from "prop-types";
import ReactTable from "react-table-6";
import { Button, ButtonToolbar, Card } from "react-bootstrap";
import NVD3Chart from "react-nvd3";
import Select from "react-dropdown-select";
import d3 from "d3";
import CodebookLabelMenuContainer from "../../containers/codebookLabelMenu_container";

const COLUMNS = [
    {
        Header: "id",
        accessor: "id",
        show: false
    },
    {
        Header: "metadata",
        accessor: "metadata",
        show: false
    },
    {
        Header: "Unlabeled Data",
        accessor: "data",
        filterMethod: (filter, row) => {
            if (
                String(row["data"])
                    .toLowerCase()
                    .includes(filter.value.toLowerCase())
            ) {
                return true;
            } else {
                return false;
            }
        }
    }
];

class Skew extends React.Component {
    componentDidMount() {
        this.props.getUnlabeled();
        this.props.getLabelCounts();
    }

    getText(row) {
        if (row.row["metadata"].length == 0) {
            return <p></p>;
        } else {
            return (
                <div>
                    <u>Background Data</u>
                    {row.row["metadata"].map(val => (
                        <p key={val}>{val}</p>
                    ))}
                    <u>Text to Label</u>
                </div>
            );
        }
    }

    render() {
        const { unlabeled_data, labels, skewLabel, label_counts } = this.props;

        let labelsOptions = labels.map(label =>
            Object.assign(label, { value: label["pk"] })
        );

        return (
            <div>
                <div className="row">
                    <div className="col-md-6">
                        <h3>Instructions</h3>
                        <p>
                            This page allows an admin to manually search for and
                            annotate data in the case of a particularly bad data
                            skew.
                        </p>
                        <p>
                            To the left is a chart that shows the distribution
                            of labels in the project. Below is all of the
                            unlabeled data that are not in a queue.
                        </p>
                        <p>
                            To annotate, click on a data entry below and select
                            the label from the expanded list of labels. As you
                            label data the chart to the left will update.
                        </p>
                    </div>
                    <div className="col-md-6">
                        <Card id="chart_panel">
                            <NVD3Chart
                                id="label_counts"
                                type="multiBarChart"
                                datum={label_counts}
                                duration={300}
                                groupSpacing={0.1}
                                stacked={true}
                                height={300}
                                yAxis={{
                                    axisLabel: "Number of Data Annotated",
                                    axisLabelDistance: -5,
                                    tickFormat: d3.format(",.01f")
                                }}
                                xAxis={{
                                    axisLabel: "Label",
                                    axisLabelDistance: 15,
                                    showMaxMin: false
                                }}
                                noData="Insufficient labeled data"
                                margin={{
                                    bottom: 20,
                                    left: 70
                                }}
                            />
                        </Card>
                    </div>
                </div>
                <CodebookLabelMenuContainer />
                <ReactTable
                    data={unlabeled_data}
                    columns={COLUMNS}
                    filterable={true}
                    showPageSizeOptions={false}
                    pageSize={
                        unlabeled_data.length < 50 ? unlabeled_data.length : 50
                    }
                    SubComponent={row => {
                        return (
                            <div className="sub-row">
                                {this.getText(row)}
                                <p id="skew_text">{row.row.data}</p>
                                <div id="skew_buttons">
                                    <ButtonToolbar variant="btn-toolbar pull-right">
                                        {labels.length > 5 ? (
                                            <Select
                                                className="align-items-center flex py-1 px-2"
                                                dropdownHandle={false}
                                                labelField="name"
                                                onChange={value =>
                                                    skewLabel(
                                                        row.row.id,
                                                        value[0]["pk"]
                                                    )
                                                }
                                                options={labelsOptions}
                                                placeholder="Select label..."
                                                searchBy="name"
                                                sortBy="name"
                                                style={{ minWidth: "200px" }}
                                            />
                                        ) : (
                                            labels.map(opt => (
                                                <Button
                                                    onClick={() =>
                                                        skewLabel(
                                                            row.row.id,
                                                            opt["pk"]
                                                        )
                                                    }
                                                    variant="primary"
                                                    key={
                                                        opt["pk"].toString() +
                                                        "_" +
                                                        row.row.id.toString()
                                                    }
                                                >
                                                    {opt["name"]}
                                                </Button>
                                            ))
                                        )}
                                    </ButtonToolbar>
                                </div>
                            </div>
                        );
                    }}
                />
            </div>
        );
    }
}

//This component will have
//data for the table
//data for the graph
//accessors for both
Skew.propTypes = {
    getUnlabeled: PropTypes.func.isRequired,
    unlabeled_data: PropTypes.arrayOf(PropTypes.object),
    labels: PropTypes.arrayOf(PropTypes.object),
    skewLabel: PropTypes.func.isRequired,
    getLabelCounts: PropTypes.func.isRequired,
    label_counts: PropTypes.arrayOf(PropTypes.object)
};

export default Skew;
