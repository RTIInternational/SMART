import React from 'react';
import { connect } from 'react-redux';

import { getHistory, changeLabel, changeToSkip } from '../actions/history';
import History from '../components/History';

const PROJECT_ID = window.PROJECT_ID;

const HistoryContainer = (props) => <History {...props} />;

const mapStateToProps = (state) => {
    return {
        history_data: state.history.history_data,
        labels: state.card.labels,
        hasExplicit: state.smart.hasExplicit
    };
};

const mapDispatchToProps = (dispatch) => {
    return {
        getHistory: () => {
            dispatch(getHistory(PROJECT_ID));
        },
        changeLabel: (dataID, oldLabelID, labelID, labelReason) => {
            dispatch(
                changeLabel(
                    dataID,
                    oldLabelID,
                    labelID,
                    labelReason,
                    PROJECT_ID
                )
            );
        },
        changeToSkip: (dataID, oldLabelID, labelID, labelReason, is_explicit) => {
            dispatch(
                changeToSkip(
                    dataID,
                    oldLabelID,
                    labelID,
                    labelReason,
                    is_explicit,
                    PROJECT_ID
                )
            );
        }
    };
};

export default connect(mapStateToProps, mapDispatchToProps)(HistoryContainer);
