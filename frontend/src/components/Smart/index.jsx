import React from 'react';
import PropTypes from 'prop-types';
import { Button, ButtonToolbar, Clearfix, Well, Tooltip, OverlayTrigger, ProgressBar } from "react-bootstrap";
import Card from '../Card';
class Smart extends React.Component {

  componentWillMount() {
      this.props.fetchCards();
  }

  render(){
    const { message, cards, passCard, annotateCard, fetchCards } = this.props;

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
    if (!(cards === undefined) && cards.length > 0) {
      var card = (
      <Card className="full" key={cards[0].id}>
          <h2>Card {cards[0].id + 1}</h2>
          <p>
              { cards[0].text['text'] }
          </p>
          <ButtonToolbar bsClass="btn-toolbar pull-right">
              {cards[0].options.map( (opt) => (
                  <Button onClick={() => annotateCard(cards[0], opt['pk'])} bsStyle="primary" key={`deck-button-${opt['name']}`}>{opt['name']}</Button>
              ))}
              <OverlayTrigger
              placement = "top"
              overlay={
                <Tooltip id="skip_tooltip">
                  Clicking this button will send this document to an administrator for review
                </Tooltip>
              }>
                <Button onClick={() => passCard(cards[0])} bsStyle="info">Skip</Button>
              </OverlayTrigger>
          </ButtonToolbar>
          <Clearfix />
      </Card>);
    }
    else {
        let blankDeckMessage = (message) ? message : "No more data to label at this time. Please check back later";
        card = (
            <Well bsSize="large">
                { blankDeckMessage }
            </Well>
        );
    }

    return (
        <div className="deck">
          <ProgressBar >
            <ProgressBar
            style={{minWidth: 60}}
            label={label}
            now={progress}/>
          </ProgressBar>
            {card}
        </div>
    );

  };
}
Smart.propTypes = {
  fetchCards: PropTypes.func.isRequired,
  annotateCard: PropTypes.func.isRequired,
  passCard: PropTypes.func.isRequired,
  popCard: PropTypes.func.isRequired,
  cards: PropTypes.arrayOf(PropTypes.object),
  message: PropTypes.string
};

export default Smart;
