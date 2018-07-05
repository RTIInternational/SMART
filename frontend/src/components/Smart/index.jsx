import React from 'react';
import PropTypes from 'prop-types';
import Deck from '../Deck';
import LabelInfo from '../LabelInfo';

const Smart = ({fetchCards, annotateCard, passCard, popCard, labels, cards, message, getLabels}) => (
    <div>
      <LabelInfo
        getLabels={getLabels}
        labels={labels}
      />
      <Deck
        fetchCards={fetchCards}
        annotateCard={annotateCard}
        passCard={passCard}
        popCard={popCard}
        cards={cards}
        message={message}
      />
    </div>
);

Smart.propTypes = {
    cards: PropTypes.arrayOf(PropTypes.object),
    message: PropTypes.string,
    labels: PropTypes.arrayOf(PropTypes.object)
};

export default Smart;
