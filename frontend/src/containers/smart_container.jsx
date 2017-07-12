import React from 'react';
import { connect } from 'react-redux';

import { fetchCards, passCard, popCard } from '../actions/classifier';
import { login, logout } from '../actions/auth';

import Smart from '../components/Smart';

const mapStateToProps = (state) => {
    return {
        cards: state.classifier.cards,
        token: state.auth.token
    };
};

const mapDispatchToProps = (dispatch) => {
    return {
        fetchCards: () => {
            dispatch(fetchCards())
        },
        passCard: () => {
            dispatch(passCard())
        },
        popCard: () => {
            dispatch(popCard())
        },
        login: (data) => {
            dispatch(login(data))
        },
        logout: () => {
            dispatch(logout())
        },
    };
};

export default connect(mapStateToProps, mapDispatchToProps)(Smart);
