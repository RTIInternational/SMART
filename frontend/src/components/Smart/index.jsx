import React from 'react';
import PropTypes from 'prop-types';
import { ProgressBar } from "react-bootstrap";
import Deck from '../Deck';
import LabelInfo from '../LabelInfo';
import { Button, Modal, ButtonGroup } from "react-bootstrap";
import PDF from 'react-pdf-js';
const CODEBOOK_URL = window.CODEBOOK_URL;

class Smart extends React.Component {

constructor(props){
  super(props);
  this.getPDF = this.getPDF.bind(this);
  this.toggleCodebook = this.toggleCodebook.bind(this);
  this.nextPage = this.nextPage.bind(this);
  this.prevPage = this.prevPage.bind(this);
  this.onDocumentComplete = this.onDocumentComplete.bind(this);
  this.getPagination = this.getPagination.bind(this);
  this.state = {
    codebook_open: false,
    codebook_page: 1,
    num_codebook_pages: 0
  }
}

//This function runs when the PDF is loaded to get the number of pages
onDocumentComplete(pages){
  this.setState({num_codebook_pages: pages});
}

//This opens/closes the codebook module
toggleCodebook(){
  this.setState({codebook_open: !this.state.codebook_open,
  codebook_page: 1});
}

//This changes the page of the codebook
nextPage(){
  this.setState({codebook_page: this.state.codebook_page + 1});
}

//This changes the page of the codebook
prevPage(){
  this.setState({codebook_page: this.state.codebook_page - 1});
}

//This returns the previous and next buttons for the codebook
getPagination()
{
  var nextButton = false;
  var prevButton = false;
  if(!(this.state.codebook_page === this.state.num_codebook_pages))
  {
    nextButton = true;
  }
  if(!(this.state.codebook_page === 1))
  {
    prevButton = true;
  }

  return (
    <ButtonGroup>
      <Button onClick={this.prevPage} disabled={!prevButton}>Previous Page</Button>
      <Button onClick={this.nextPage} disabled={!nextButton}>Next Page</Button>
    </ButtonGroup>
  );
}

//This renders the PDF in the modal if one exists for the project
getPDF()
{
  if(CODEBOOK_URL != "")
  {


    return (
      <div>
        <Button onClick={this.toggleCodebook}>Codebook</Button>
        <Modal show={this.state.codebook_open} onHide={this.toggleCodebook}>
          <Modal.Header closeButton>
            <Modal.Title>Codebook</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <PDF
            file={CODEBOOK_URL}
            onDocumentComplete={this.onDocumentComplete}
            page={this.state.codebook_page}/>
            {this.getPagination()}
          </Modal.Body>
        </Modal>
      </div>
    );
  }
  else {
    return (<p>No Codebook</p>);
  }
}

render()
{
  const { message, cards, passCard, annotateCard, popCard, fetchCards, labels, getLabels } = this.props;
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
      {this.getPDF()}
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
}

Smart.propTypes = {
    cards: PropTypes.arrayOf(PropTypes.object),
    message: PropTypes.string,
    labels: PropTypes.arrayOf(PropTypes.object)
};

export default Smart;
