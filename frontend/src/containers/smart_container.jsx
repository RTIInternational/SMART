import React from 'react';
import { connect } from 'react-redux';
import { fetchCards, passCard, popCard } from '../actions/classifier';

import Smart from '../components/Smart';

class SmartContainer extends React.Component {
    componentWillMount() {
        this.props.fetchCards();
    }

    render() {
        return (
            <Smart {...this.props} />
        );
    }
};

const mapStateToProps = (state) => {
    return {
        cards: state.classifier.cards
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
        }
    };
};

export default connect(mapStateToProps, mapDispatchToProps)(SmartContainer);