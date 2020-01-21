import React from 'react';
import { connect } from 'react-redux';

import { fetchCards, annotateCard, passCard } from '../actions/card';
import Card from '../components/Card';

const PROJECT_ID = window.PROJECT_ID;
const ADMIN = window.ADMIN;

const CardContainer = (props) => <Card {...props} />;

const mapStateToProps = (state) => {
    return {
        cards: state.card.cards,
        message: state.card.message,
        labels: state.card.labels,
        hasExplicit: state.smart.hasExplicit
    };
};

const mapDispatchToProps = (dispatch) => {
    return {
        fetchCards: () => {
            dispatch(fetchCards(PROJECT_ID));
        },
        annotateCard: (dataID, labelID, labelReason, num_cards_left) => {
            dispatch(
                annotateCard(
                    dataID,
                    labelID,
                    labelReason,
                    num_cards_left,
                    PROJECT_ID,
                    ADMIN
                )
            );
        },
        passCard: (dataID, labelID, labelReason, num_cards_left, is_explicit) => {
            dispatch(
                passCard(
                    dataID,
                    labelID,
                    labelReason,
                    num_cards_left,
                    is_explicit,
                    PROJECT_ID,
                    ADMIN
                )
            );
        }
    };
};

export default connect(mapStateToProps, mapDispatchToProps)(CardContainer);
