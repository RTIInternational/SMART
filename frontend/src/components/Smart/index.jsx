import React from 'react';
import PropTypes from 'prop-types';
import { Tabs, Tab } from "react-bootstrap";

import Deck from '../Deck';
import HistoryTable from '../HistoryTable';
import Skew from '../Skew';
const ADMIN = window.ADMIN

const Smart = ({fetchCards, annotateCard,
  passCard, popCard, cards, message,
  getHistory, history_data, labels, changeLabel,
  changeToSkip, getUnlabeled, unlabeled_data,
  skewLabel, getLabelCounts, label_counts}) => (
    <Tabs defaultActiveKey={1} id="data_tabs">
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
          changeToSkip={changeToSkip}
        />
      </Tab>
      <Tab eventKey={3} disabled={!ADMIN} title="Fix Skew">
        <Skew
        getUnlabeled={getUnlabeled}
        unlabeled_data={unlabeled_data}
        labels={labels}
        skewLabel={skewLabel}
        getLabelCounts={getLabelCounts}
        label_counts={label_counts}
        />
      </Tab>
    </Tabs>
);

Smart.propTypes = {
    cards: PropTypes.arrayOf(PropTypes.object),
    message: PropTypes.string,
    history_data: PropTypes.arrayOf(PropTypes.object),
    labels: PropTypes.arrayOf(PropTypes.object),
    label_counts: PropTypes.arrayOf(PropTypes.object)
};

export default Smart;
