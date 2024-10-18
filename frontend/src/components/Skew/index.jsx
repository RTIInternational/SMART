import React from "react";
import PropTypes from "prop-types";
import ReactTable from "react-table-6";
import { Card } from "react-bootstrap";
import NVD3Chart from "react-nvd3";
import d3 from "d3";
import CodebookLabelMenuContainer from "../../containers/codebookLabelMenu_container";
import DataCard, { PAGES } from "../DataCard/DataCard";

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
        accessor: "data"
    }
];

class Skew extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            filteredData: undefined,
            isSearching: false,
            search: '',
        };
        this.handleSearch = this.handleSearch.bind(this);
    }

    componentDidMount() {
        this.props.setFilterStr("");
        this.props.getUnlabeled();
        //this.props.getLabelCounts();
    }

    getText(row) {
        if (row.row["metadata"].length == 0) {
            return <p></p>;
        } else {
            return (
                <div>
                    <u>Respondent Data</u>
                    {row.row["metadata"].map(val => (
                        <p key={val}>{val}</p>
                    ))}
                    <u>Text to Label</u>
                </div>
            );
        }
    }

    handleSearch(event) {
        event.preventDefault();
        this.props.setFilterStr(this.state.search);
        this.props.getUnlabeled();
    }

    render() {
        const { unlabeled_data, skewLabel, label_counts, message } = this.props;

        if (message.length > 0){
            let message_new = message[0];
            if (message_new.includes("ERROR")){
                return (<div>{message_new}</div>);
            }
        }

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
                <p>
                    View the unlabeled data for this project in the table below.<br/>
                    Note: The first 50 unlabeled data items appear in the table. If you are looking for a specific value, use the search input to filter the data.
                </p>
                <form onSubmit={this.handleSearch}>
                    <input 
                        className="skew-input" 
                        onChange={event => this.setState({ search: event.target.value })} 
                        placeholder="Search Data..." 
                        value={this.state.search} 
                    />
                    {!this.state.isSearching ? (
                        <button className="btn btn-info skew-search-button" type="submit">Search</button>
                    ) : (
                        <p style={{ marginBottom: '8px', marginTop: '8px' }}>Searching unlabeled data for {this.state.search}...</p>
                    )}
                </form>
                <ReactTable
                    data={unlabeled_data}
                    columns={COLUMNS}
                    showPageSizeOptions={false}
                    pageSize={
                        unlabeled_data.length < 50 ? unlabeled_data.length : 50
                    }
                    SubComponent={row => {
                        return (
                            <div className="sub-row cardface clearfix">
                                <DataCard 
                                    data={row.original}
                                    page={PAGES.SKEW} 
                                    actions={{ onSelectLabel: skewLabel }} 
                                />
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
    label_counts: PropTypes.arrayOf(PropTypes.object),
    message: PropTypes.string,
    modifyMetadataValues: PropTypes.func.isRequired,
    setFilterStr: PropTypes.func.isRequired,
};

export default Skew;
