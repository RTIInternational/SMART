import React from 'react';
import { connect } from 'react-redux';

import { getUnlabeled } from '../actions/skew';

import UnlabeledDataStatus from '../components/UnlabeledDataStatus';

const PROJECT_ID = window.PROJECT_ID;

const UnlabeledDataStatusContainer = (props) => <UnlabeledDataStatus {...props} />;

const mapStateToProps = (state) => {
    return {
        unlabeled_data: state.skew.unlabeled_data
    };
};

const mapDispatchToProps = (dispatch) => {
    return {
        getUnlabeled: () => {
            dispatch(getUnlabeled(PROJECT_ID));
        },
    };
};

export default connect(mapStateToProps, mapDispatchToProps)(UnlabeledDataStatusContainer);
