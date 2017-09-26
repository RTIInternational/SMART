import React from 'react';
import { connect } from 'react-redux';

import { fetchCards, passCard, popCard } from '../actions/classifier';

import Smart from '../components/Smart';

const QUEUE_ID = window.QUEUE_ID

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
            dispatch(fetchCards(QUEUE_ID))
        },
        passCard: () => {
            dispatch(passCard())
        },
        popCard: () => {
            dispatch(popCard())
        }
    };
};

export default connect(mapStateToProps, mapDispatchToProps)(SmartContainer);
