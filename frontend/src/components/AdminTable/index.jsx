import React from "react";
import PropTypes from "prop-types";
import ReactTable from "react-table-6";
import {
    Button,
    ButtonToolbar,
    Tooltip,
    OverlayTrigger
} from "react-bootstrap";
import Select from "react-dropdown-select";
import CodebookLabelMenuContainer from "../../containers/codebookLabelMenu_container";

class AdminTable extends React.Component {
    componentDidMount() {
        this.props.getAdmin();
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
        const { admin_data, labels, adminLabel, discardData } = this.props;

        let labelsOptions = labels.map(label =>
            Object.assign(label, { value: label["pk"] })
        );

        const columns = [
            {
                Header: "id",
                accessor: "id",
                show: false
            },
            {
                Header: "Reason",
                accessor: "reason",
                show: true,
                width: 70
            },
            {
                Header: "metadata",
                accessor: "metadata",
                show: false
            },
            {
                Header: "Unlabeled Data",
                accessor: "data",
                Cell: row => (
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
                            <div id="admin_buttons">
                                {labels.length > 5 ? (
                                    <Select
                                        className="absolute align-items-center flex py-1 px-2"
                                        dropdownHandle={false}
                                        labelField="name"
                                        onChange={value =>
                                            adminLabel(
                                                row.row.id,
                                                value[0]["pk"]
                                            )
                                        }
                                        options={labelsOptions}
                                        placeholder="Select label..."
                                        searchBy="name"
                                        sortBy="name"
                                        style={{
                                            position: "absolute",
                                            minWidth: "200px",
                                            width: "fit-content"
                                        }}
                                    />
                                ) : (
                                    labels.map(opt => (
                                        <Button
                                            onClick={() =>
                                                adminLabel(
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
                                <OverlayTrigger
                                    placement="top"
                                    overlay={
                                        <Tooltip id="discard_tooltip">
                                            This marks this data as uncodable,
                                            and will remove it from the active
                                            data in this project.
                                        </Tooltip>
                                    }
                                >
                                    <Button
                                        key={"discard_" + row.row.id.toString()}
                                        onClick={() => discardData(row.row.id)}
                                        variant="danger"
                                        style={{ marginLeft: "205px" }}
                                    >
                                        Discard
                                    </Button>
                                </OverlayTrigger>
                            </div>
                        </ButtonToolbar>
                    </div>
                )
            }
        ];

        let page_sizes = [1];
        for (let i = 5; i < admin_data.length; i += 5) {
            page_sizes.push(i);
        }
        page_sizes.push(admin_data.length);

        return (
            <div>
                <h3>Instructions</h3>
                <p>
                    This page allows an admin to label data that was skipped by
                    labelers, or was disagreed upon in inter-rater reliability
                    checks.
                </p>
                <CodebookLabelMenuContainer />
                <ReactTable
                    data={admin_data}
                    columns={columns}
                    pageSizeOptions={page_sizes}
                    defaultPageSize={1}
                    filterable={false}
                />
                <style>
                    {
                        "\
                    .react-dropdown-select-dropdown {\
                        min-width: 200px;\
                        width: fit-content;\
                    }\
                "
                    }
                </style>
            </div>
        );
    }
}

AdminTable.propTypes = {
    getAdmin: PropTypes.func.isRequired,
    admin_data: PropTypes.arrayOf(PropTypes.object),
    labels: PropTypes.arrayOf(PropTypes.object),
    adminLabel: PropTypes.func.isRequired,
    discardData: PropTypes.func.isRequired
};

export default AdminTable;
