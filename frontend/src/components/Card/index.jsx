import React from 'react';
import PropTypes from 'prop-types';
import { Button, ButtonToolbar, Clearfix, Well, Tooltip, OverlayTrigger } from "react-bootstrap";

const ADMIN = window.ADMIN;


class Card extends React.Component {

    componentWillMount() {
        this.props.fetchCards();
    }

    render() {
        let card;
        const { labels, message, cards, passCard, annotateCard } = this.props;

        if (!(cards === undefined) && cards.length > 0) {
            //just get the labels from the cards
            card = (
                <div className="full" key={cards[0].id}>
                    <div className="cardface">
                        <h2>Card {cards[0].id + 1}</h2>
                        <p>{ cards[0].text['text'] }</p>
                        <ButtonToolbar bsClass="btn-toolbar pull-right">
                            {labels.map( (opt) => (
                                <Button onClick={() => annotateCard(cards[0], opt['pk'], cards.length, ADMIN)}
                                    bsStyle="primary"
                                    key={`deck-button-${opt['name']}`}>{opt['name']}</Button>
                            ))}
                            <OverlayTrigger
                                placement = "top"
                                overlay={
                                    <Tooltip id="skip_tooltip">
                                        Clicking this button will send this document to an administrator for review
                                    </Tooltip>
                                }>
                                <Button onClick={() => {
                                    passCard(cards[0], cards.length, ADMIN);
                                }}
                                bsStyle="info">Skip</Button>
                            </OverlayTrigger>
                        </ButtonToolbar>
                        <Clearfix />
                    </div>
                </div>);
        } else {
            let blankDeckMessage = (message) ? message : "No more data to label at this time. Please check back later";
            card = (
                <Well bsSize="large">
                    { blankDeckMessage }
                </Well>
            );
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
};

export default Card;
