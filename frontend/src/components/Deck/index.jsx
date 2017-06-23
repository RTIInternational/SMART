import React from 'react';
import { Button, ButtonToolbar, Clearfix, Well } from "react-bootstrap";

import Card from '../Card';
import Container from '../container';

const SCALE_FACTOR = 400;

const Deck = ({ cards, passCard, popCard }) => {
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
                    <div style={{
                        padding: '16px 24px',
                        margin: '16px 24px',
                        border: '1px solid #ccc'
                    }}>
                        <h2>Card {card.id + 1}</h2>
                        <p>
                            Card content
                        </p>
                        <ButtonToolbar bsClass="btn-toolbar pull-right">
                            {card.options.map( (opt) => (
                                <Button onClick={popCard} bsStyle="primary">Classification {opt}</Button>
                            ))}
                            { cardCount > 1 && 
                                <Button onClick={passCard} bsStyle="secondary">Skip</Button>
                            }
                            { cardCount == 1 && 
                                <Button onClick={passCard} bsStyle="secondary" disabled={true}>Skip</Button>
                            }
                        </ButtonToolbar>
                        <Clearfix />
                    </div>
                </Card>
            );
        });
    }
    else {
        deck = (
            <Well bsSize="large">
                No more Cards! Please check again later.
            </Well>
        );
    }
    
    return (
        <div className="deck">
            {deck}
        </div>
    );
};

export default Deck;