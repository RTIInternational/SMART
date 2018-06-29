import React from 'react';
import { connect } from 'react-redux';

import { fetchCards, annotateCard, passCard, popCard } from '../actions/classifier';

import Smart from '../components/Smart';

const PROJECT_ID = window.PROJECT_ID

const SmartContainer = (props) => <Smart {...props} />;

const mapStateToProps = (state) => {
    return {
        cards: state.classifier.cards,
        message: state.classifier.message
    };
};

const mapDispatchToProps = (dispatch) => {
    return {
        fetchCards: () => {
            dispatch(fetchCards(PROJECT_ID))
        },
        annotateCard: (dataID, labelID) => {
            dispatch(annotateCard(dataID, labelID))
        },
        passCard: (dataID) => {
            dispatch(passCard(dataID))
        },
        popCard: () => {
            dispatch(popCard())
        },
    };
};

export default connect(mapStateToProps, mapDispatchToProps)(SmartContainer);
