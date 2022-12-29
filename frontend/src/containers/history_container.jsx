import React from 'react';
import { connect } from 'react-redux';

import { getHistory, changeLabel, changeToSkip, verifyDataLabel } from '../actions/history';
import History from '../components/History';

const PROJECT_ID = window.PROJECT_ID;

const HistoryContainer = (props) => <History {...props} />;

const mapStateToProps = (state) => {
    return {
        history_data: state.history.history_data,
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
        verifyDataLabel: (dataID) => {
            dispatch(verifyDataLabel(dataID, PROJECT_ID));
        }
    };
};

export default connect(mapStateToProps, mapDispatchToProps)(HistoryContainer);
