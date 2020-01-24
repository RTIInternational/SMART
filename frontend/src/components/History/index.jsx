import React from 'react';
import PropTypes from 'prop-types';
import ReactTable from 'react-table';
import {
    Alert
} from 'react-bootstrap';
import CodebookLabelMenuContainer from '../../containers/codebookLabelMenu_container';
import DataViewer from '../DataViewer';
import LabelForm from '../LabelForm';



class History extends React.Component {


    componentWillMount() {
        this.props.getHistory();
    }

    getSubComponent(row) {
        let subComponent;
        const { labels, changeToSkip, changeLabel, hasExplicit } = this.props;

        if (row.row.edit === "yes") {
            subComponent = (
                <div className="sub-row">
                    <DataViewer data={this.props.history_data[row.row._index]} />
                    <LabelForm
                        data={row.row.id}
                        previousLabel={{
                            pk: row.row.old_label_id,
                            name: row.row.old_label,
                            reason: row.row.label_reason,
                            is_explicit: row.row.is_explicit
                        }}
                        labelFunction={changeLabel}
                        passButton={true}
                        discardButton={false}
                        skipFunction={changeToSkip}
                        discardFunction={() => {}}
                        labels={labels}
                        hasExplicit={hasExplicit}
                    />
                </div>
            );
        } else {
            subComponent = (
                <div className="sub-row">
                    <DataViewer data={this.props.history_data[row.row._index]} />
                    <Alert bsStyle="warning">
                        <strong>Note:</strong>
                        This is Inter-rater Reliability data and is not editable.
                    </Alert>
                </div>
            );
        }

        return subComponent;
    }

    render() {

        const { history_data } = this.props;
        const COLUMNS = [
            {
                Header: "edit",
                accessor: "edit",
                show: false
            },
            {
                Header: "id",
                accessor: "id",
                show: false
            },
            {
                Header: "Data",
                accessor: "data",
                filterMethod: (filter, row) => {
                    if (String(row["data"]).toLowerCase().includes(filter.value.toLowerCase())) {
                        return true;
                    } else {
                        return false;
                    }
                }
            },
            {
                Header: "Old Label",
                accessor: "old_label",
                width: 100
            },
            {
                Header: "Reason for Label",
                accessor: "label_reason",
                width: 200
            },
            {
                Header: "Old Label ID",
                accessor: "old_label_id",
                show: false
            },
            {
                Header: "Date/Time",
                accessor: "timestamp",
                id: "timestamp",
                width: 150
            },
            {
                Header: "Explicit",
                accessor: "is_explicit",
                show: false
            }
        ];


        let page_sizes = [1];
        let counter = 1;
        for (let i = 5; i < history_data.length; i += 5 * counter) {
            page_sizes.push(i);
            counter += 1;
        }
        page_sizes.push(history_data.length);

        return (
            <div>
                <h3>Instructions</h3>
                <p>This page allows a coder to change past labels.</p>
                <p>
                    To annotate, click on a data entry below and select the
                    label from the expanded list of labels. The chart will then
                    update with the new label and current timestamp{" "}
                </p>
                <p>
                    <strong>NOTE:</strong> Data labels that are changed on this
                    page will not effect past model accuracy or data selected by
                    active learning in the past. The training data will only be
                    updated for the next run of the model
                </p>

                <CodebookLabelMenuContainer />
                <ReactTable
                    data={history_data}
                    columns={COLUMNS}
                    pageSize={(history_data.length < 50) ? history_data.length : 50}
                    showPageSizeOptions={false}
                    SubComponent={row => this.getSubComponent(row)}
                    filterable={true}
                    defaultSorted={[
                        {
                            id: "timestamp",
                            desc: true
                        }
                    ]}
                />
            </div>
        );
    }
}

//This component will have
// change label (action)
// change_to_skip (action)
// data
History.propTypes = {
    labels: PropTypes.arrayOf(PropTypes.object),
    getHistory: PropTypes.func.isRequired,
    history_data: PropTypes.arrayOf(PropTypes.object),
    changeLabel: PropTypes.func.isRequired,
    changeToSkip: PropTypes.func.isRequired,
    hasExplicit: PropTypes.boolean
};

export default History;
