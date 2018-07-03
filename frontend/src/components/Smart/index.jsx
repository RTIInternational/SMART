import React from 'react';
import PropTypes from 'prop-types';
import { Tabs, Tab } from "react-bootstrap";

import Deck from '../Deck';
import HistoryTable from '../HistoryTable';

const Smart = ({fetchCards, annotateCard,
  passCard, popCard, cards, message,
  getHistory, history_data, labels, changeLabel}) => (
    <Tabs defaultActiveKey={1}>
      <Tab eventKey={1} title="Annotate Data">
        <Deck
            fetchCards={fetchCards}
            annotateCard={annotateCard}
            passCard={passCard}
            popCard={popCard}
            cards={cards}
            message={message}
            getHistory={getHistory}
        />
      </Tab>
      <Tab eventKey={2} title="History">
        <HistoryTable
          getHistory={getHistory}
          history_data={history_data}
          labels={labels}
          changeLabel={changeLabel}
        />
      </Tab>
    </Tabs>
);

Smart.propTypes = {
    cards: PropTypes.arrayOf(PropTypes.object),
    message: PropTypes.string,
    history_data: PropTypes.arrayOf(PropTypes.object),
    labels: PropTypes.arrayOf(PropTypes.string)
};

export default Smart;
