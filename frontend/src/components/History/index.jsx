import React from "react";
import PropTypes from "prop-types";
import ReactTable from "react-table-6";
import { Button, Alert, Modal, OverlayTrigger, Tooltip } from "react-bootstrap";
import CodebookLabelMenuContainer from "../../containers/codebookLabelMenu_container";
import AnnotateCard, { buildCard } from "../AnnotateCard";
import EditableMetadataCell from "./EditableMetadataCell";



class History extends React.Component {
    constructor() {
        super();
        this.toggleConfirm = this.toggleConfirm.bind(this);
        this.verifyLabel = this.verifyLabel.bind(this);
        this.historyChangeLabel = this.historyChangeLabel.bind(this);
        this.state = {
            pageSize : parseInt(localStorage.getItem("pageSize") || "25"),
            showConfirm : false
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
                Header: "Verified",
                width: 80,
                accessor: "verified",
                Cell: props => {
                    if (props.value == "Yes") {
                        return (<p>Yes</p>);
                    } else {
                        return (<Button variant="success" value={props.row.id} onClick={this.verifyLabel}>Verify</Button>);
                    }
                }
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
            }
        ];
    }

    toggleConfirm() {
        this.setState({ showConfirm : !this.state.showConfirm });
    }

    componentDidMount() {
        this.props.getHistory();
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
        const { labels, changeToSkip } = this.props;
        const card = buildCard(row.row.id, null, row.original);

        if (row.row.edit === "yes") {
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

    render() {
        const { history_data } = this.props;

        let metadataColumns = [];
        history_data.forEach((data) => {
            if (data.formattedMetadata)
                Object.keys(data.formattedMetadata).forEach((metadataColumn) =>
                    !metadataColumns.includes(metadataColumn) ? metadataColumns.push(metadataColumn) : null
                );
        });

        let page_sizes = [1];
        let counter = 1;
        for (let i = 5; i < history_data.length; i += 5 * counter) {
            page_sizes.push(i);
            counter += 1;
        }
        page_sizes.push(history_data.length);

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

        return (
            <div className="history">
                <h3>Instructions</h3>
                <p>This page allows a coder to change past labels.</p>
                <p style={{ maxWidth: "75ch" }}>
                    To annotate, click on a data entry below and select the
                    label from the expanded list of labels. The chart will then
                    update with the new label and current timestamp{" "}
                </p>
                <p style={{ maxWidth: "75ch" }}>
                    <strong>NOTE:</strong> Data labels that are changed on this
                    page will not effect past model accuracy or data selected by
                    active learning in the past. The training data will only be
                    updated for the next run of the model
                </p>
                <p style={{ maxWidth: "75ch" }}>
                    <strong>TIP:</strong> In this table you may edit metadata fields. Click on the value in the column and row where you want to change the data and it will open as a text box.
                </p>
                <CodebookLabelMenuContainer />
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
                            show: true,
                            Cell: (props) => (
                                <EditableMetadataCell id={props.row._original.metadataIDs[i]} modifyMetadataValue={this.props.modifyMetadataValue} value={props.value} />
                            ),
                        };
                    })]}
                    showPageSizeOptions={true}
                    pageSizeOptions={[5, 10, 25, 50, 100]}
                    defaultPageSize={this.state.pageSize}
                    onPageSizeChange={(pageSize) => localStorage.setItem("pageSize", pageSize)}
                    SubComponent={row => this.getSubComponent(row)}
                    filterable={true}
                    defaultSorted={[
                        {
                            id: "timestamp",
                            desc: true
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
    history_data: PropTypes.arrayOf(PropTypes.object),
    changeLabel: PropTypes.func.isRequired,
    changeToSkip: PropTypes.func.isRequired,
    verifyDataLabel: PropTypes.func.isRequired,
    modifyMetadataValue: PropTypes.func.isRequired
};

export default History;
