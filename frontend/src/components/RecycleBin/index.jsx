import React from 'react';
import PropTypes from 'prop-types';
import ReactTable from 'react-table-6';
import { Button, ButtonToolbar, Tooltip, OverlayTrigger } from "react-bootstrap";
import CodebookLabelMenuContainer from '../../containers/codebookLabelMenu_container';

const COLUMNS = [
    {
        Header: "id",
        accessor: "id",
        show: false
    },
    {
        Header: "Discarded Data",
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


class RecycleBin extends React.Component {

    componentDidMount() {
        this.props.getDiscarded();
    }

    getSubComponent(row) {
        const { restoreData } = this.props;

        return (
            <div className="sub-row">
                <p id="disc_text">{row.row.data}</p>
                <div id="disc_buttons">
                    <ButtonToolbar bsClass="btn-toolbar pull-right">
                        <OverlayTrigger
                            placement = "top"
                            overlay={
                                <Tooltip id="discard_tooltip">
                                    This will add this data back into the project active data.
                                </Tooltip>
                            }>
                            <Button onClick = {() => restoreData(row.row.id)}
                                bsStyle="danger">Restore</Button>
                        </OverlayTrigger>
                    </ButtonToolbar>
                </div>
            </div>
        );
    }

    render() {
        const { discarded_data } = this.props;

        return (
            <div>
                <h3>Instructions</h3>
                <p>This page displays all data that has been discarded by an admin.</p>
                <p>All data in this table has been removed from the set of unlabeled data to be predicted, and will not be assigned to anyone for labeling.</p>
                <p>To add a datum back into the project, click the Restore button next to the datum.</p>
                <CodebookLabelMenuContainer />
                <ReactTable
                    data={discarded_data}
                    columns={COLUMNS}
                    showPageSizeOptions={false}
                    pageSize={(discarded_data.length < 50) ? discarded_data.length : 50}
                    filterable={true}
                    SubComponent={row => this.getSubComponent(row)}
                />
            </div>
        );
    }
}

RecycleBin.propTypes = {
    getDiscarded: PropTypes.func.isRequired,
    discarded_data: PropTypes.arrayOf(PropTypes.object),
    restoreData: PropTypes.func.isRequired,
};

export default RecycleBin;
