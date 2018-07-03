import React from 'react';
import PropTypes from 'prop-types';
import { ProgressBar } from "react-bootstrap";
import Deck from '../Deck';

const Smart = ({fetchCards, annotateCard, passCard, popCard, cards, message }) => {
  var progress = 100;
  var start_card = 0;
  var num_cards = 0;
  if(!(cards === undefined) && cards.length > 0)
  {
      num_cards = cards[cards.length-1].id + 1;
      start_card = cards[0].id + 1;
      progress = (cards[0].id/cards[cards.length-1].id) * 100;
  }
  return(
    <div>
      <ProgressBar >
        <ProgressBar
        style={{minWidth: 60}}
        label={start_card.toString()+" out of "+num_cards.toString()}
        now={progress}/>
      </ProgressBar>
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
