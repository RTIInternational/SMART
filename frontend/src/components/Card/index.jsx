import React from 'react';
import PropTypes from 'prop-types';
import {
    Well
} from "react-bootstrap";

import DataViewer from "../DataViewer";
import LabelForm from '../LabelForm';

class Card extends React.Component {

    componentWillMount() {
        //Don't fetch cards unless you don't have any
        //NOTE: otherwise it appends the same cards
        //to the current list again.
        if (this.props.cards.length == 0) {
            this.props.fetchCards();
        }
    }

    render() {
        let card;
        const { message, cards, passCard, labels, annotateCard, hasExplicit } = this.props;

        if (!(cards === undefined) && cards.length > 0) {
            //just get the labels from the cards
            card = (
                <div className="full" key={cards[0].id}>
                    <div className="cardface">
                        <h2>Card {cards[0].id + 1}</h2>
                        <DataViewer data={cards[0]} />
                        <LabelForm
                            data={cards[0]}
                            labelFunction={annotateCard}
                            passButton={true}
                            discardButton={false}
                            skipFunction={passCard}
                            discardFunction={() => {}}
                            labels={labels}
                            optionalInt={cards.length}
                            hasExplicit = {hasExplicit}
                            labelingTab="annotate"
                        />
                    </div>
                </div>
            );
        } else {
            let blankDeckMessage = message ? message : "No more data to label at this time. Please check back later";
            card = <Well bsSize="large"> {blankDeckMessage} </Well>;
        }

        return card;
    }
}

Card.propTypes = {
    cards: PropTypes.arrayOf(PropTypes.object),
    message: PropTypes.string,
    fetchCards: PropTypes.func.isRequired,
    annotateCard: PropTypes.func.isRequired,
    passCard: PropTypes.func.isRequired,
    labels: PropTypes.arrayOf(PropTypes.object),
    hasExplicit: PropTypes.boolean
};

export default Card;
