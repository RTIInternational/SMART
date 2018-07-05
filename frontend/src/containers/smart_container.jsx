import React from 'react';
import { connect } from 'react-redux';

import { fetchCards, annotateCard, passCard, popCard } from '../actions/classifier';
import { getHistory, changeLabel, changeToSkip } from '../actions/history';
import { getUnlabeled, skewLabel, getLabelCounts } from '../actions/adminTables';
import Smart from '../components/Smart';

const PROJECT_ID = window.PROJECT_ID

const SmartContainer = (props) => <Smart {...props} />;

const mapStateToProps = (state) => {
    return {
        cards: state.classifier.cards,
        message: state.classifier.message,
        history_data: state.history.history_data,
        labels: state.history.labels,
        unlabeled_data: state.adminTables.unlabeled_data,
        label_counts: state.adminTables.label_counts
    };
};

const mapDispatchToProps = (dispatch) => {
    return {
        fetchCards: () => {
            dispatch(fetchCards(PROJECT_ID))
        },
        annotateCard: (dataID, labelID) => {
            dispatch(annotateCard(dataID, labelID, PROJECT_ID))
        },
        passCard: (dataID) => {
            dispatch(passCard(dataID))
        },
        popCard: () => {
            dispatch(popCard())
        },
        getHistory: () => {
            dispatch(getHistory(PROJECT_ID))
        },
        changeLabel: (dataID, oldLabelID ,labelID) => {
            dispatch(changeLabel(dataID, oldLabelID, labelID, PROJECT_ID))
        },
        changeToSkip: (dataID, oldLabelID) => {
            dispatch(changeToSkip(dataID, oldLabelID, PROJECT_ID))
        },
        getUnlabeled: () => {
          dispatch(getUnlabeled(PROJECT_ID))
        },
        skewLabel: (dataID, labelID) => {
            dispatch(skewLabel(dataID, labelID, PROJECT_ID))
        },
        getLabelCounts: () => {
            dispatch(getLabelCounts(PROJECT_ID))
        }
    };
};

export default connect(mapStateToProps, mapDispatchToProps)(SmartContainer);
