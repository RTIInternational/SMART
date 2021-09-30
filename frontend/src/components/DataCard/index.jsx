import React from "react";
import PropTypes from "prop-types";
import {
    Card
} from "react-bootstrap";
import AnnotateCard from "../AnnotateCard";

const ADMIN = window.ADMIN;

class DataCard extends React.Component {
    componentDidMount() {
        //Don't fetch cards unless you don't have any
        //NOTE: otherwise it appends the same cards
        //to the current list again.
        if (this.props.cards.length == 0) {
            this.props.fetchCards();
        }
    }

    render() {
        let card;

        const { labels, message, cards, passCard, annotateCard } = this.props;

        if (!(cards === undefined) && cards.length > 0) {
            //just get the labels from the cards
            card = (
                <div className="full" key={cards[0].id}>
                    <AnnotateCard
                        card={cards[0]}
                        labels={labels}
                        onSelectLabel={(card, label) =>
                            annotateCard(
                                card,
                                label,
                                cards.length,
                                ADMIN
                            )}
                        onSkip={(card) => passCard(card, cards.length, ADMIN)}
                    />
                </div>
            );
        } else {
            let blankDeckMessage = message
                ? message
                : "No more data to label at this time. Please check back later";
            card = <Card body>{blankDeckMessage}</Card>;
        }

        return card;
    }
}

DataCard.propTypes = {
    cards: PropTypes.arrayOf(PropTypes.object),
    message: PropTypes.string,
    fetchCards: PropTypes.func.isRequired,
    annotateCard: PropTypes.func.isRequired,
    passCard: PropTypes.func.isRequired,
    labels: PropTypes.arrayOf(PropTypes.object)
};

export default DataCard;
