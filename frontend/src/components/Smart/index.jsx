import React from 'react';
import PropTypes from 'prop-types';

import { Button } from "react-bootstrap";

import Deck from '../Deck';

const Smart = ({fetchCards, passCard, popCard, cards }) => (
    <Deck 
        fetchCards={fetchCards}
        passCard={passCard}
        popCard={popCard}
        cards={cards}
    />
);

Smart.propTypes = {
    cards: PropTypes.arrayOf(PropTypes.object)
};

export default Smart;
