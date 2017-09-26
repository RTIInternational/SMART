import React from 'react';
import PropTypes from 'prop-types';

import Deck from '../Deck';

const Smart = ({fetchCards, passCard, popCard, cards, message }) => (
    <Deck 
        fetchCards={fetchCards}
        passCard={passCard}
        popCard={popCard}
        cards={cards}
        message={message}
    />
);

Smart.propTypes = {
    cards: PropTypes.arrayOf(PropTypes.object),
    message: PropTypes.string
};

export default Smart;
