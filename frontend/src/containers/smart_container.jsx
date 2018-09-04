import React from 'react';
import { connect } from 'react-redux';

import { fetchCards, annotateCard, passCard, popCard,
    getAdminTabsAvailable, getAdminCounts } from '../actions/classifier';
import Smart from '../components/Smart';

const PROJECT_ID = window.PROJECT_ID;

const SmartContainer = (props) => <Smart {...props} />;

const mapStateToProps = (state) => {
    return {
        cards: state.classifier.cards,
        message: state.classifier.message,
        adminTabsAvailable: state.classifier.adminTabsAvailable,
        admin_counts: state.classifier.admin_counts,
        labels: state.classifier.labels
    };
};

const mapDispatchToProps = (dispatch) => {
    return {
        fetchCards: () => {
            dispatch(fetchCards(PROJECT_ID));
        },
        annotateCard: (dataID, labelID, num_cards_left, is_admin) => {
            dispatch(annotateCard(dataID, labelID, num_cards_left, PROJECT_ID, is_admin));
        },
        passCard: (dataID, num_cards_left, is_admin) => {
            dispatch(passCard(dataID, num_cards_left, is_admin, PROJECT_ID));
        },
        popCard: () => {
            dispatch(popCard());
        },
        getAdminTabsAvailable: () => {
            dispatch(getAdminTabsAvailable(PROJECT_ID));
        },
        getAdminCounts: () => {
            dispatch(getAdminCounts(PROJECT_ID));
        }
    };
};

export default connect(mapStateToProps, mapDispatchToProps)(SmartContainer);
