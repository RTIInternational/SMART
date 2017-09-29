import React from 'react';
import { Button, ButtonToolbar, Clearfix, Well } from "react-bootstrap";

import Card from '../Card';
import PropTypes from 'prop-types';

const SCALE_FACTOR = 400;

class Deck extends React.Component {
    componentWillMount() {
        this.props.fetchCards();
    }
    
    render() {
        const { message, cards, passCard, popCard, annotateCard } = this.props;
        const cardCount = cards.length;

        let deck;
        if (cardCount > 0) {
            deck = cards.map( (card, i) => {
                let style = {
                    position: 'absolute',
                    padding: 0,
                    zIndex: cardCount - i
                };

                let translate = `${i * 4}px`;

                if (i >= 10) {
                    translate = `${10 * 4}px`;
                }

                style.transform = `translateY(${translate}) scale(${(SCALE_FACTOR - i) / SCALE_FACTOR})`;

                return (
                    <Card className="full" style={style} key={card.id}>
                        <h2>Card {card.id + 1}</h2>
                        <p>
                            { card.text[1] }
                        </p>
                        <ButtonToolbar bsClass="btn-toolbar pull-right">
                            {card.options.map( (opt) => (
                                <Button onClick={() => annotateCard(card.text[0], opt[0], card.queue_id)} bsStyle="primary" key={`deck-button-${opt[1]}`}>{opt[1]}</Button>
                            ))}
                            { cardCount > 1 && 
                                <Button onClick={passCard} bsStyle="info">Skip</Button>
                            }
                            { cardCount == 1 && 
                                <Button onClick={passCard} bsStyle="info" disabled={true}>Skip</Button>
                            }
                        </ButtonToolbar>
                        <Clearfix />
                    </Card>
                );
            });
        }
        else {
            deck = (
                <Well bsSize="large">
                    {message}
                </Well>
            );
        }
        
        return (
            <div className="deck">
                {deck}
            </div>
        );
    }
}

Deck.propTypes = {
    fetchCards: PropTypes.func.isRequired,
    annotateCard: PropTypes.func.isRequired,
    passCard: PropTypes.func.isRequired,
    popCard: PropTypes.func.isRequired,
    cards: PropTypes.arrayOf(PropTypes.object),
    message: PropTypes.string
};

export default Deck;
