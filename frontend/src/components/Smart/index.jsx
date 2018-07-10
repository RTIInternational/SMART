import React from 'react';
import PropTypes from 'prop-types';
import { ProgressBar } from "react-bootstrap";
import Deck from '../Deck';
import LabelInfo from '../LabelInfo';
import { Button, Modal } from "react-bootstrap";
import PDF from 'react-pdf-js';
const CODEBOOK_URL = window.CODEBOOK_URL;

function getPDF(){
  if(CODEBOOK_URL != "")
  {
    return (<PDF file={CODEBOOK_URL} page={1}/>);
  }
  else {
    return (<p>No Codebook</p>);
  }
}

const Smart = ({fetchCards, annotateCard,
  passCard, popCard, cards, message,
  labels, getLabels}) => {
  var progress = 100;
  var start_card = 0;
  var num_cards = 0;
  var label = "Complete";
  if(!(cards === undefined) && cards.length > 0)
  {
      num_cards = cards[cards.length-1].id + 1;
      start_card = cards[0].id + 1;
      progress = (cards[0].id/cards[cards.length-1].id) * 100;
      label = start_card.toString()+" out of "+num_cards.toString();
  }

  return(
    <div>
      <ProgressBar >
        <ProgressBar
        style={{minWidth: 60}}
        label={label}
        now={progress}/>
      </ProgressBar>
      {getPDF()}
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
}

Smart.propTypes = {
    cards: PropTypes.arrayOf(PropTypes.object),
    message: PropTypes.string,
    labels: PropTypes.arrayOf(PropTypes.object)
};

export default Smart;
