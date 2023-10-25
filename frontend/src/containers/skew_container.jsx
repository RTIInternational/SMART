import React from 'react';
import { connect } from 'react-redux';
import { modifyMetadataValues } from '../actions/card';

import { getUnlabeled, skewLabel, getLabelCounts } from '../actions/skew';
import Skew from '../components/Skew';

const PROJECT_ID = window.PROJECT_ID;

const SkewContainer = (props) => <Skew {...props} />;

const mapStateToProps = (state) => {
    return {
        unlabeled_data: state.skew.unlabeled_data,
        label_counts: state.skew.label_counts,
        labels: state.smart.labels,
        message: state.card.message
    };
};

const mapDispatchToProps = (dispatch) => {
    return {
        getUnlabeled: () => {
            dispatch(getUnlabeled(PROJECT_ID));
        },
        skewLabel: ({ dataID, selectedLabelID }) => {
            dispatch(skewLabel(dataID, selectedLabelID, PROJECT_ID));
        },
        getLabelCounts: () => {
            dispatch(getLabelCounts(PROJECT_ID));
        },
        modifyMetadataValues: (dataPk, metadatas) => {
            dispatch(modifyMetadataValues(dataPk, metadatas, PROJECT_ID));
        }
    };
};

export default connect(mapStateToProps, mapDispatchToProps)(SkewContainer);
