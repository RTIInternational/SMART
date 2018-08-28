import React from 'react';
import { connect } from 'react-redux';

import { fetchCards, annotateCard, passCard, popCard } from '../actions/classifier';
import { getHistory, changeLabel, changeToSkip } from '../actions/history';
import { getUnlabeled, skewLabel, getLabelCounts,
    adminLabel, getAdmin, discardData, getDiscarded,
    restoreData, getAdminTabsAvailable, getAdminCounts } from '../actions/adminTables';
import Smart from '../components/Smart';

const PROJECT_ID = window.PROJECT_ID;

const SmartContainer = (props) => <Smart {...props} />;

const mapStateToProps = (state) => {
    return {
        cards: state.classifier.cards,
        message: state.classifier.message,
        history_data: state.history.history_data,
        unlabeled_data: state.adminTables.unlabeled_data,
        label_counts: state.adminTables.label_counts,
        admin_data: state.adminTables.admin_data,
        discarded_data: state.adminTables.discarded_data,
        available: state.adminTables.available,
        labels: state.classifier.labels,
        admin_counts: state.adminTables.admin_counts
    };
};

const mapDispatchToProps = (dispatch) => {
    return {
        fetchCards: () => {
            dispatch(fetchCards(PROJECT_ID))
        },
        annotateCard: (dataID, labelID, num_cards_left, is_admin) => {
            dispatch(annotateCard(dataID, labelID, num_cards_left, PROJECT_ID, is_admin))
        },
        passCard: (dataID, num_cards_left, is_admin) => {
            dispatch(passCard(dataID, num_cards_left, is_admin, PROJECT_ID))
        },
        popCard: () => {
            dispatch(popCard())
        },
        getHistory: () => {
            dispatch(getHistory(PROJECT_ID))
        },
        changeLabel: (dataID, oldLabelID, labelID) => {
            dispatch(changeLabel(dataID, oldLabelID, labelID, PROJECT_ID))
        },
        changeToSkip: (dataID, oldLabelID) => {
            dispatch(changeToSkip(dataID, oldLabelID, PROJECT_ID))
        },
        getAdminTabsAvailable: () => {
            dispatch(getAdminTabsAvailable(PROJECT_ID))
        },
        getUnlabeled: () => {
            dispatch(getUnlabeled(PROJECT_ID))
        },
        skewLabel: (dataID, labelID) => {
            dispatch(skewLabel(dataID, labelID, PROJECT_ID))
        },
        getLabelCounts: () => {
            dispatch(getLabelCounts(PROJECT_ID))
        },
        adminLabel: (dataID, labelID) => {
            dispatch(adminLabel(dataID, labelID, PROJECT_ID))
        },
        getAdmin: () => {
            dispatch(getAdmin(PROJECT_ID))
        },
        discardData: (dataID) => {
            dispatch(discardData(dataID, PROJECT_ID))
        },
        restoreData: (dataID) => {
            dispatch(restoreData(dataID, PROJECT_ID))
        },
        getDiscarded: () => {
            dispatch(getDiscarded(PROJECT_ID))
        },
        getAdminCounts: () => {
            dispatch(getAdminCounts(PROJECT_ID))
        }
    };
};

export default connect(mapStateToProps, mapDispatchToProps)(SmartContainer);
