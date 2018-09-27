import React from 'react';
import PropTypes from 'prop-types';
import { ProgressBar } from "react-bootstrap";


class SmartProgressBar extends React.Component {

    componentWillMount() {
    }

    render() {
        let { cards } = this.props;
        let progress = 100;
        let start_card = 0;
        let num_cards = 0;
        let label = "Complete";
        if (!(cards === undefined) && cards.length > 0) {
            num_cards = cards[cards.length - 1].id + 1;
            start_card = cards[0].id + 1;
            progress = (cards[0].id / cards[cards.length - 1].id) * 100;
            label = start_card.toString() + " of " + num_cards.toString();
        }

        return (
            <ProgressBar>
                <ProgressBar
                    style={{ minWidth: 60 }}
                    label={label}
                    now={progress}/>
            </ProgressBar>
        );
    }
}

SmartProgressBar.propTypes = {
    cards: PropTypes.arrayOf(PropTypes.object),
};

export default SmartProgressBar;
