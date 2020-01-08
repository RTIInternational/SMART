import React from 'react';
import PropTypes from 'prop-types';
import ReactTable from 'react-table';
import { Panel } from 'react-bootstrap';
import NVD3Chart from 'react-nvd3';
import d3 from 'd3';
import CodebookLabelMenuContainer from '../../containers/codebookLabelMenu_container';
import DataViewer from "../DataViewer";
import LabelForm from '../LabelForm';

const COLUMNS = [
    {
        Header: "id",
        accessor: "id",
        show: false
    },
    {
        Header: "Unlabeled Data",
        accessor: "data",
        filterMethod: (filter, row) => {
            if (String(row["data"]).toLowerCase().includes(filter.value.toLowerCase())) {
                return true;
            } else {
                return false;
            }
        }
    }
];

class Skew extends React.Component {
    componentWillMount() {
        this.props.getUnlabeled();
        this.props.getLabelCounts();
    }

    renderTable(){
        const { unlabeled_data, skewLabel, labels } = this.props;
        if (unlabeled_data.length == 0) {
            return <b>Loading unlabeled data. This may take up to a minute for large datasets..</b>;
        } else {
            return (<ReactTable
                data={unlabeled_data}
                columns={COLUMNS}
                filterable={true}
                showPageSizeOptions={false}
                pageSize={(unlabeled_data.length < 50) ? unlabeled_data.length : 50}
                SubComponent={row => {
                    return (
                        <div className="sub-row">
                            <DataViewer data={unlabeled_data[row.row._index]} />
                            <LabelForm
                                data={row.row.id}
                                labelFunction={skewLabel}
                                passButton={false}
                                discardButton={false}
                                skipFunction={() => {}}
                                discardFunction={() => {}}
                                labels={labels}
                            />
                        </div>
                    );
                }}
            />);
        }
    }

    render() {
        const { unlabeled_data, label_counts } = this.props;

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
                        <Panel id="chart_panel">
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
                                    tickFormat: d3.format(',.01f')
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
                        </Panel>
                    </div>
                </div>
                <CodebookLabelMenuContainer />
                {this.renderTable()}
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
