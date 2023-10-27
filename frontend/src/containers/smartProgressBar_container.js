import React from 'react';
import { connect } from 'react-redux';

import SmartProgressBar from '../components/SmartProgressBar';


const SmartProgressBarContainer = (props) => <SmartProgressBar {...props} />;

const mapStateToProps = (state) => {
    return {
        labels: state.smart.labels,
        cards: state.card.cards
    };
};

export default connect(mapStateToProps)(SmartProgressBarContainer);
