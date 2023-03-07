import React from 'react';
import { connect } from 'react-redux';

import { getHistory, changeLabel, changeToSkip, modifyMetadataValue } from '../actions/history';
import History from '../components/History';

const PROJECT_ID = window.PROJECT_ID;

const HistoryContainer = (props) => <History {...props} />;

const mapStateToProps = (state) => {
    return {
        history_data: state.history.history_data,
        unlabeled_data: state.history.unlabeled_data,
        labels: state.card.labels
    };
};

const mapDispatchToProps = (dispatch) => {
    return {
        getHistory: () => {
            dispatch(getHistory(PROJECT_ID));
        },
        changeLabel: (dataID, oldLabelID, labelID) => {
            dispatch(changeLabel(dataID, oldLabelID, labelID, PROJECT_ID));
        },
        changeToSkip: (dataID, oldLabelID, message) => {
            dispatch(changeToSkip(dataID, oldLabelID, PROJECT_ID, message));
        },
        modifyMetadataValue: (metadataId, value) => {
            dispatch(modifyMetadataValue(metadataId, value));
        }
    };
};

export default connect(mapStateToProps, mapDispatchToProps)(HistoryContainer);
