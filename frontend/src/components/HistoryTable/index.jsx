import React from 'react';
import PropTypes from 'prop-types';
import ReactTable from 'react-table';
import {Button, ButtonToolbar, Tooltip, OverlayTrigger} from "react-bootstrap";
import CodebookLabelMenu from '../CodebookLabelMenu';
const columns = [
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
            if(String(row["data"]).toLowerCase().includes(filter.value.toLowerCase())) {
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
        Header: "Old Label ID",
        accessor: "old_label_id",
        show: false
    },
    {
        Header: "Date/Time",
        accessor: "timestamp",
        id: "timestamp",
        width: 150
    }
];


class HistoryTable extends React.Component {

    componentWillMount() {
        this.props.getHistory();
    }


    render() {
        const {history_data, labels, changeLabel, changeToSkip} = this.props;

        if(history_data) {
            var table_data = history_data
        } else {
            table_data = []
        }

        var page_sizes = [1];
        var counter = 1;
        for(var i = 5; i < table_data.length; i += 5 * counter) {
            page_sizes.push(i);
            counter += 1;
        }
        page_sizes.push(table_data.length);

        return (
            <div>
                <h3>Instructions</h3>
                <p>This page allows a coder to change past labels.</p>
                <p>To annotate, click on a data entry below and select the label from the expanded list of labels. The chart will then update with the new label and current timestamp </p>
                <p><strong>NOTE:</strong> Data labels that are changed on this page will not effect past model accuracy or data selected by active learning in the past. The training data will only be updated for the next run of the model</p>
                <CodebookLabelMenu
                    labels={labels}
                />
                <ReactTable
                    data={table_data}
                    columns={columns}
                    pageSize={(table_data.length < 50) ? table_data.length : 50}
                    showPageSizeOptions={false}
                    SubComponent={row => {

                        if(row.row.edit === "yes") {
                            return (
                                <div className="sub-row">
                                    <p>{row.row.data}</p>
                                    <ButtonToolbar bsClass="btn-toolbar pull-right">
                                        {labels.map( (label) => {
                                            return (
                                                <Button key={label.pk.toString() + "_" + row.row.id.toString()}
                                                    onClick={() => {
                                                        if(!(row.row.old_label_id === label.pk)) {
                                                            changeLabel(row.row.id, row.row.old_label_id, label.pk)
                                                        }
                                                    }}
                                                    bsStyle="primary"
                                                >{label.name}</Button>
                                            )
                                        })}
                                        <OverlayTrigger
                                            placement = "top"
                                            overlay={
                                                <Tooltip id="skip_tooltip">
                  Clicking this button will send this document to an administrator for review
                                                </Tooltip>
                                            }>
                                            <Button onClick={() => changeToSkip(row.row.id, row.row.old_label_id)}
                                                bsStyle="info"
                                            >Skip</Button>
                                        </OverlayTrigger>
                                    </ButtonToolbar>
                                </div>
                            );
                        } else {
                            return (
                                <div className="sub-row">
                                    <p>{row.row.data}</p>
                                    <p id="irr_history_message">Note: This is Inter-rater Reliability data and is not editable.</p>
                                </div>
                            );
                        }
                    }}
                    filterable={true}
                    defaultSorted={[{
                        id: "timestamp",
                        desc: true
                    }]}

                />
            </div>
        )
    }

}


//This component will have
// change label (action)
// change_to_skip (action)
// data
HistoryTable.propTypes = {
    getHistory: PropTypes.func.isRequired,
    history_data: PropTypes.arrayOf(PropTypes.object),
    labels: PropTypes.arrayOf(PropTypes.object),
    changeLabel: PropTypes.func.isRequired,
    changeToSkip: PropTypes.func.isRequired
};

export default HistoryTable;
