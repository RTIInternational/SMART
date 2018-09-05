import React from 'react';
import { connect } from 'react-redux';

import SmartProgressBar from '../components/SmartProgressBar';


const SmartProgressBarContainer = (props) => <SmartProgressBar {...props} />;

const mapStateToProps = (state) => {
    return {
        labels: state.card.labels,
        cards: state.card.cards
    };
};

const mapDispatchToProps = (dispatch) => {
    return {
    };
};

export default connect(mapStateToProps, mapDispatchToProps)(SmartProgressBar);
