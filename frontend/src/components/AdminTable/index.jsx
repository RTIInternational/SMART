import React from "react";
import PropTypes from "prop-types";
import ReactTable from "react-table-6";
import CodebookLabelMenuContainer from "../../containers/codebookLabelMenu_container";
import DataCard, { PAGES } from "../DataCard/DataCard";
import IRRtable from "./IRRtable";

class AdminTable extends React.Component {
    componentDidMount() {
        this.props.getAdmin();
        this.props.getIrrLog();
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

    render() {
        const { admin_data, irr_log, labels, message, adminLabel, discardData } = this.props;

        const getIrrEntry = data_id => {
            const irr_entry = irr_log.find(entry => entry.data_id === data_id);
            if (irr_entry) return irr_entry;
            return {};
        };

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
                Cell: row => {
                    return (
                        <div className="sub-row">
                            {row.original.message && (
                                <div className="adjudicate-message">
                                    <h4>Reason for skipping:</h4>
                                    <p style={{ whiteSpace: "normal" }}>{row.original.message}</p>
                                </div>
                            )}
                            <div className="admin-data-card-wrapper">                            
                                <DataCard 
                                    data={row.original}
                                    page={PAGES.ADMIN} 
                                    actions={{ onSelectLabel: adminLabel, onDiscard: discardData }} 
                                />
                                { row.original.reason === "IRR" &&
                                    <IRRtable irrEntry={getIrrEntry(row.original.id)} />
                                }
                            </div>
                        </div>
                    );
                }
            },
            // column for coder, label table
            
        ];

        let page_sizes = [1];
        for (let i = 5; i < admin_data.length; i += 5) {
            page_sizes.push(i);
        }
        page_sizes.push(admin_data.length);

        if (message.length > 0){
            let message_new = message[0];
            if (message_new.includes("ERROR")){
                return (<div>{message_new}</div>);
            }
        }

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
                    .rt-td {\
                        overflow-y: auto !important;\
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
    message: PropTypes.string,
    adminLabel: PropTypes.func.isRequired,
    discardData: PropTypes.func.isRequired
};

export default AdminTable;
