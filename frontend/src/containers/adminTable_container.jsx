import React from 'react';
import { connect } from 'react-redux';

import { adminLabel, getAdmin, discardData } from '../actions/adminTables';
import AdminTable from '../components/AdminTable';

const PROJECT_ID = window.PROJECT_ID;

const AdminTableContainer = (props) => <AdminTable {...props} />;

const mapStateToProps = (state) => {
    return {
        admin_data: state.adminTables.admin_data,
        labels: state.card.labels,
        message: state.card.message,
        admin_counts: state.adminTables.admin_counts
    };
};

const mapDispatchToProps = (dispatch) => {
    return {
        adminLabel: ({ dataID, selectedLabelID }) => {
            dispatch(adminLabel(dataID, selectedLabelID, PROJECT_ID));
        },
        getAdmin: () => {
            dispatch(getAdmin(PROJECT_ID));
        },
        discardData: (dataID) => {
            dispatch(discardData(dataID, PROJECT_ID));
        }
    };
};

export default connect(mapStateToProps, mapDispatchToProps)(AdminTableContainer);
