import React from 'react';
import PropTypes from 'prop-types';
import ReactTable from 'react-table';
import { Button, ButtonToolbar, Tooltip, OverlayTrigger } from "react-bootstrap";
import CodebookLabelMenuContainer from '../../containers/codebookLabelMenu_container';


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
                            <ButtonToolbar bsClass="btn-toolbar pull-right">
                                {labels.map( (label) => {
                                    return (
                                        <Button key={label.pk.toString() + "_" + row.row.id.toString()}
                                            onClick={() => adminLabel(row.row.id, label.pk)}
                                            bsStyle="primary"
                                        >{label.name}
                                        </Button>
                                    );
                                })}
                                <OverlayTrigger
                                    placement = "top"
                                    overlay={
                                        <Tooltip id="discard_tooltip">
                                            This marks this data as uncodable, and will remove it from the active data in this project.
                                        </Tooltip>
                                    }>
                                    <Button
                                        key={"discard_" + row.row.id.toString()}
                                        onClick={() => discardData(row.row.id)}
                                        bsStyle="danger">
                                        Discard
                                    </Button>
                                </OverlayTrigger>
                            </ButtonToolbar>
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
                <p>This page allows an admin to label data that was skipped by labelers, or was disagreed upon in inter-rater reliability checks.</p>
                <CodebookLabelMenuContainer />
                <ReactTable
                    data={admin_data}
                    columns={columns}
                    pageSizeOptions={page_sizes}
                    defaultPageSize={1}
                    filterable={false} />
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
