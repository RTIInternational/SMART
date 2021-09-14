import React from "react";
import PropTypes from "prop-types";
import ReactTable from "react-table-6";
import {
    Button,
    ButtonToolbar,
    Tooltip,
    OverlayTrigger,
    Alert
} from "react-bootstrap";
import Select from "react-dropdown-select";
import CodebookLabelMenuContainer from "../../containers/codebookLabelMenu_container";

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

class History extends React.Component {
    componentDidMount() {
        this.props.getHistory();
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
                    <u>Background Data</u>
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
        const { labels, changeLabel, changeToSkip } = this.props;

        let labelsOptions = labels.map(label =>
            Object.assign(label, { value: label["pk"] })
        );

        if (row.row.edit === "yes") {
            subComponent = (
                <div className="sub-row cardface cardface-datacard clearfix">
                    <div className="cardface-info">
                        {this.getText(row)}
                        <p>{row.row.data}</p>
                    </div>
                    {labels.length > 5 && (
                        <div className="suggestions">
                            <h4>Suggested Labels</h4>
                            {row.original.similarityPair.slice(0, 5).map((opt, index) => (
                                <div key={index + 1} className="">{index + 1}. {opt.split(':')[0]}</div>
                            ))}
                        </div>
                    )}
                    <ButtonToolbar variant="btn-toolbar pull-right">
                        {labels.length > 5 ? (
                            <Select
                                className="align-items-center flex py-1 px-2"
                                dropdownHandle={false}
                                labelField="dropdownLabel"
                                onChange={value =>
                                    changeLabel(
                                        row.row.id,
                                        row.row.old_label_id,
                                        value[0]["pk"]
                                    )
                                }
                                options={labelsOptions}
                                placeholder="Select label..."
                                searchBy="dropdownLabel"
                                sortBy="dropdownLabel"
                                style={{ minWidth: "200px" }}
                            />
                        ) : (
                            <React.Fragment>
                                {labels.map(label =>
                                    this.getLabelButton(row, label)
                                )}
                            </React.Fragment>
                        )}
                        <OverlayTrigger
                            placement="top"
                            overlay={
                                <Tooltip id="skip_tooltip">
                                    Clicking this button will send this document
                                    to an administrator for review
                                </Tooltip>
                            }
                        >
                            <Button
                                onClick={() =>
                                    changeToSkip(
                                        row.row.id,
                                        row.row.old_label_id
                                    )
                                }
                                variant="info"
                            >
                                Skip
                            </Button>
                        </OverlayTrigger>
                    </ButtonToolbar>
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

    render() {
        const { history_data } = this.props;

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
                    pageSize={
                        history_data.length < 50 ? history_data.length : 50
                    }
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
    changeToSkip: PropTypes.func.isRequired
};

export default History;
