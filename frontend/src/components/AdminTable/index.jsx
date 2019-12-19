import React from "react";
import PropTypes from "prop-types";
import ReactTable from "react-table";
import CodebookLabelMenuContainer from "../../containers/codebookLabelMenu_container";
import LabelForm from "../LabelForm";

class AdminTable extends React.Component {
    componentWillMount() {
        this.props.getAdmin();
    }

    render() {
        const { admin_data, labels, adminLabel, discardData } = this.props;

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
                Header: "Unlabeled Data",
                accessor: "data",
                Cell: row => (
                    <div>
                        <p id="admin_text">{row.row.data}</p>
                        <div id="admin_buttons">
                            <LabelForm
                                data={row.row.id}
                                labelFunction={adminLabel}
                                passButton={false}
                                discardButton={true}
                                skipFunction={() => {}}
                                discardFunction={discardData}
                                labels={labels}
                            />
                        </div>
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
