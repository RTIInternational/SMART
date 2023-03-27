import React from "react";
import PropTypes from "prop-types";
import ReactTable from "react-table-6";
import { Button, Alert, Modal, OverlayTrigger, Tooltip } from "react-bootstrap";
import CodebookLabelMenuContainer from "../../containers/codebookLabelMenu_container";
import AnnotateCard, { buildCard } from "../AnnotateCard";
import Select from "react-dropdown-select";


class History extends React.Component {
    constructor() {
        super();
        this.toggleConfirm = this.toggleConfirm.bind(this);
        this.verifyLabel = this.verifyLabel.bind(this);
        this.historyChangeLabel = this.historyChangeLabel.bind(this);
        this.createFilterForm = this.createFilterForm.bind(this);
        this.changeFilterValue = this.changeFilterValue.bind(this);
        this.filterHistory = this.filterHistory.bind(this);
        this.resetFilters = this.resetFilters.bind(this);
        this.state = {
            pageSize : parseInt(localStorage.getItem("pageSize") || "25"),
            showConfirm: false,
            temp_filters: { Text:"" }
        };
        this.cardID, this.rowID, this.label;
    }

    COLUMNS() {
        return [
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
                Header: "hidden",
                accessor: "metadata",
                show: false
            },
            {
                Header: "Data",
                accessor: "data",
                filterMethod: (filter, row) => {
                    if (
                        String(row.data)
                            .toLowerCase()
                            .includes(filter.value.toLowerCase())
                    ) {
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
                Header: "User",
                accessor: "profile",
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
            },
            {
                Header: "Verified",
                width: 80,
                accessor: "verified",
                Cell: props => {
                    if (props.value == "Yes") {
                        return (<p>Yes</p>);
                    } else if (props.value != "No") {
                        return (<p>{props.value}</p>);
                    } else {
                        return (<Button variant="success" value={props.row.id} onClick={this.verifyLabel}>Verify</Button>);
                    }
                }
            },
            {
                Header: "Verified By",
                accessor: "verified_by",
                width: 100
            },
            {
                Header: "Pre-Loaded",
                width: 100,
                accessor: "pre_loaded"
            }
        ];
    }

    toggleConfirm() {
        this.setState({ showConfirm : !this.state.showConfirm });
    }

    componentDidMount() {
        this.props.getHistory();
    }

    componentDidUpdate(prevProps, prevState) {
        if (prevProps.metadata_fields != this.props.metadata_fields) {
            // Only populate this once
            if (this.props.metadata_fields.length > 0 && Object.keys(this.state.temp_filters).length == 1) {
                let temp = { Text: this.state.temp_filters.Text };
                this.props.metadata_fields.map(field => {
                    temp[field] = "";
                });
                this.setState({ 
                    temp_filters: temp
                });
            }
        }
    }

    toggleShowUnlabeled() {
        this.props.toggleUnlabeled();
    }

    verifyLabel(event) {
        this.props.verifyDataLabel(event.target.value);
    }

    getLabelButton(row, label) {
        const { changeLabel } = this.props;

        if (row.row.old_label_id === label.pk) {
            return (
                <Button
                    key={label.pk.toString() + "_" + row.row.id.toString()}
                    variant="primary"
                    disabled
                >
                    {label.name}
                </Button>
            );
        } else {
            return (
                <Button
                    key={label.pk.toString() + "_" + row.row.id.toString()}
                    onClick={() =>
                        changeLabel(row.row.id, row.row.old_label_id, label.pk)
                    }
                    variant="primary"
                >
                    {label.name}
                </Button>
            );
        }
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

    getSubComponent(row) {
        let subComponent;
        const { labels, changeToSkip, changeLabel } = this.props;
        const card = buildCard(row.row.id, null, row.original);

        if (row.row.edit === "yes" && (row.row.old_label === "")) {
            subComponent = (
                <div className="sub-row cardface clearfix">
                    <AnnotateCard
                        card={card}
                        labels={labels}
                        onSelectLabel={(card, label) => {
                            changeLabel(
                                card.id,
                                undefined,
                                label
                            );
                        }}
                        onSkip={(card, message) => {
                            changeToSkip(
                                card.id,
                                undefined,
                                message
                            );
                        }}
                    />
                </div>
            );
        } else if (row.row.edit === "yes") {
            subComponent = (
                <div className="sub-row cardface clearfix">
                    <AnnotateCard
                        card={card}
                        labels={labels}
                        onSelectLabel={(card, label) => {
                            this.toggleConfirm();
                            this.cardID = card.id;
                            this.rowID = row.row.old_label_id;
                            this.label = label;
                        }}
                        onSkip={(card, message) => {
                            changeToSkip(
                                card.id,
                                row.row.old_label_id,
                                message
                            );
                        }}
                    />
                </div>
            );
        } else {
            subComponent = (
                <div className="sub-row">
                    <p>{row.row.data}</p>
                    <Alert variant="warning" transition={false}>
                        <strong>Note:</strong>
                        This is Inter-rater Reliability data and is not
                        editable.
                    </Alert>
                </div>
            );
        }

        return subComponent;
    }

    historyChangeLabel() {
        const { changeLabel } = this.props;
        this.toggleConfirm();                 
        changeLabel(
            this.cardID,
            this.rowID,
            this.label
        );
    }

    filterHistory(event) {
        // Update official filter state and re-pull history table
        event.preventDefault();
        this.props.filterHistoryTable(this.state.temp_filters);
    }

    changeFilterValue(event) {
        let temp = this.state.temp_filters;
        temp[event.target.name] = event.target.value;
        this.setState({ 
            temp_filters: temp
        });
    }

    resetFilters() {
        let current_filters = this.state.temp_filters;
        for (let key in current_filters) {
            current_filters[key] = "";
        }
        this.setState({
            temp_filters: current_filters
        });
        this.props.filterHistoryTable(this.state.temp_filters);
    }

    createFilterForm() {
        // The form contains filters for text, and any metadata field
        return (
            <div>
                <h4>Filters</h4>
                <form onSubmit={this.filterHistory}>
                    <div className="form-group history-filter">
                        <label className="control-label" style={{ marginRight: "4px" }}>Data</label>
                        <input className="form-control" type="text" name="Text" value={this.state.temp_filters.Text} onChange={this.changeFilterValue} />
                    </div>
                    {this.props.metadata_fields.map(field => {
                        return (
                            <div className="form-group history-filter" key={field}>
                                <label className="control-label" style={{ marginRight: "4px" }}>{field}</label>
                                <input className="form-control" type="text" name={field} value={this.state.temp_filters[field] || ''} onChange={this.changeFilterValue} />
                            </div>
                        );
                    })}
                    <input className="btn btn-primary" type="submit" value="Apply Filters" />
                    <Button variant="secondary" onClick={this.resetFilters}>Reset Filters</Button>
                </form>
            </div>
        );
    }

    render() {
        const { history_data, num_pages, setCurrentPage } = this.props;

        
        let paginationDropdown = (<div></div>);
        if (num_pages > 1) {
            let pageOptions = [];
            for (let i = 1; i < num_pages; i++) {
                pageOptions.push({ "value":i, "pageLabel":`Batch ${i} (${(i - 1) * 100} - ${(i) * 100})` });
            }
            pageOptions.push({ "value":num_pages, "pageLabel":`Batch ${num_pages} (${(num_pages - 1) * 100}+)` });
            paginationDropdown = (
                <div style={{ marginBottom: "1rem" }}>
                    <b>
                        NOTE: For performance reasons, SMART only returns 100 items at a time. 
                        Use the dropdown below to navigate between batches of 100 items. Items are sorted 
                        by text in alphabetical order. Recently labeled items in a batch are returned first.
                        <br />
                    </b>
                    <Select
                        className="align-items-center flex py-1 px-2 annotate-select"
                        dropdownHandle={false}
                        labelField="pageLabel"
                        onChange={(selection) => {
                            setCurrentPage(selection[0].value);
                        }}
                        options={pageOptions}
                        placeholder="Select Batch..."
                        searchBy="pageLabel"
                    />
                </div>
            );
        }
        

        let metadataColumns = [];
        history_data.forEach((data) => {
            if (data.formattedMetadata)
                Object.keys(data.formattedMetadata).forEach((metadataColumn) =>
                    !metadataColumns.includes(metadataColumn) ? metadataColumns.push(metadataColumn) : null
                );
        });

        //Confirmation button
        let confirm_message = (
            <Modal
                centered
                show={this.state.showConfirm} 
                onHide={this.toggleConfirm} animation={false}>
                <Modal.Header closeButton>
                    <Modal.Title>Confirmation</Modal.Title>
                </Modal.Header>
                <Modal.Body>Are you sure you want to change labels?</Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={this.toggleConfirm}>
                        Cancel
                    </Button>
                    <Button variant="primary" onClick={ this.historyChangeLabel }>
                        Confirm change
                    </Button>
                </Modal.Footer>
            </Modal>
        );

        let unlabeled_checkbox = (
            <div className="form-group" style={{ marginBottom: "0" }}>
                <p>
                    Toggle the checkbox below to show/hide unlabeled data:
                </p>
                <label className="control-label">
                    <span style={{ marginRight: "4px" }}>Unlabled Data</span>
                    <input type="checkbox" disabled />
                </label>
                <div>
                    <i>Unlabeled data cannot be accessed in the history table for projects using the Inter-Rater-Reliability feature.</i>
                </div>
            </div>
        );
        if (!window.PROJECT_USES_IRR) {
            unlabeled_checkbox = (
                <div className="form-group" style={{ marginBottom: "0" }}>
                    <p>
                        Toggle the checkbox below to show/hide unlabeled data:
                    </p>
                    <label className="control-label">
                        <span style={{ marginRight: "4px" }}>Unlabled Data</span>
                        <input type="checkbox" onChange={() => this.toggleShowUnlabeled()} />
                    </label>
                </div>
            );
        }

        return (
            <div className="history">
                <h3>Instructions</h3>
                <p>This page allows a coder to change past labels.</p>
                <p>
                    To annotate, click on a data entry below and select the
                    label from the expanded list of labels. The chart will then
                    update with the new label and current timestamp{" "}.
                </p>
                <p>
                    <strong>NOTE:</strong> Data labels that are changed on this
                    page will not effect past model accuracy or data selected by
                    active learning in the past. The training data will only be
                    updated for the next run of the model.
                </p>
                {/* <p style={{ maxWidth: "75ch" }}>
                    <strong>TIP:</strong> In this table you may edit metadata fields. Click on the value in the column and row where you want to change the data and it will open as a text box.
                </p> */}
                <CodebookLabelMenuContainer />
                <div className="history-filters">
                    {this.createFilterForm()}
                </div>
                <div className="history-filters">
                    {unlabeled_checkbox}
                </div>
                <div>
                    {paginationDropdown}
                </div>
                <ReactTable
                    data={history_data}
                    columns={[...this.COLUMNS(), ...metadataColumns.map((column, i) => {
                        return {
                            Header: () => (
                                <OverlayTrigger
                                    placement="top"
                                    overlay={
                                        <Tooltip id={`history-column-${column}`}>
                                            {column}
                                        </Tooltip>
                                    }
                                >
                                    <span style={{ display: "inline-block", width: "100%" }}>{column}</span>
                                </OverlayTrigger>
                            ),
                            accessor: `formattedMetadata.${column}`,
                            show: true
                        };
                    })]}
                    showPageSizeOptions={true}
                    pageSizeOptions={[5, 10, 25, 50, 100]}
                    defaultPageSize={this.state.pageSize}
                    onPageSizeChange={(pageSize) => localStorage.setItem("pageSize", pageSize)}
                    SubComponent={row => this.getSubComponent(row)}
                    defaultSorted={[
                        {
                            id: "timestamp",
                            desc: true
                        },
                        {
                            id: "data",
                            desc: false
                        }
                    ]}
                />
                {confirm_message}
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
    toggleUnlabeled: PropTypes.func.isRequired,
    setCurrentPage: PropTypes.func.isRequired,
    history_data: PropTypes.arrayOf(PropTypes.object),
    filterHistoryTable: PropTypes.func.isRequired,
    num_pages: PropTypes.number,
    metadata_fields: PropTypes.arrayOf(PropTypes.object),
    current_page: PropTypes.number,
    changeLabel: PropTypes.func.isRequired,
    changeToSkip: PropTypes.func.isRequired,
    verifyDataLabel: PropTypes.func.isRequired,
};

export default History;
