import React from 'react';
import { connect } from 'react-redux';

import { getUnlabeled, skewLabel, getLabelCounts } from '../actions/skew';
import Skew from '../components/Skew';

const PROJECT_ID = window.PROJECT_ID;

const SkewContainer = (props) => <Skew {...props} />;

const mapStateToProps = (state) => {
    return {
        unlabeled_data: state.skew.unlabeled_data,
        label_counts: state.skew.label_counts,
        labels: state.card.labels,
        message: state.card.message
    };
};

const mapDispatchToProps = (dispatch) => {
    return {
        getUnlabeled: () => {
            dispatch(getUnlabeled(PROJECT_ID));
        },
        skewLabel: (dataID, labelID) => {
            dispatch(skewLabel(dataID, labelID, PROJECT_ID));
        },
        getLabelCounts: () => {
            dispatch(getLabelCounts(PROJECT_ID));
        }
    };
};

export default connect(mapStateToProps, mapDispatchToProps)(SkewContainer);
