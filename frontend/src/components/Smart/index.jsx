import React from 'react';
import PropTypes from 'prop-types';
import { ProgressBar } from "react-bootstrap";
import Deck from '../Deck';

const Smart = ({fetchCards, annotateCard, passCard, popCard, cards, message }) => {
  var progress = 0;
  if(!(cards === undefined) && cards.length > 0)
  {
      progress = (cards[0].id/cards[cards.length-1].id) * 100;
  }
  return(
    <div>
      <ProgressBar now={progress}/>
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
}

Smart.propTypes = {
    cards: PropTypes.arrayOf(PropTypes.object),
    message: PropTypes.string
};

export default Smart;
