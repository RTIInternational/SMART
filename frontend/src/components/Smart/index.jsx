import React from 'react';
import PropTypes from 'prop-types';
import { Tabs, Tab, ProgressBar } from "react-bootstrap";

import Deck from '../Deck';
import HistoryTable from '../HistoryTable';
import Skew from '../Skew';
import AdminTable from '../AdminTable';
const ADMIN = window.ADMIN

const Smart = ({fetchCards, annotateCard,
  passCard, popCard, cards, message,
  getHistory, history_data, labels, changeLabel,
  changeToSkip, getUnlabeled, unlabeled_data,
  skewLabel, getLabelCounts, label_counts, getAdmin,
  admin_data, adminLabel}) => {
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
    return (
      <Tabs defaultActiveKey={1} id="data_tabs" >
        <Tab eventKey={1} title="Annotate Data">
          <ProgressBar >
            <ProgressBar
            style={{minWidth: 60}}
            label={label}
            now={progress}/>
          </ProgressBar>

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
        <Tab eventKey={2} title="History" className="full card">
          <div className="cardface">
          <HistoryTable
            getHistory={getHistory}
            history_data={history_data}
            labels={labels}
            changeLabel={changeLabel}
            changeToSkip={changeToSkip}
          />
          </div>
        </Tab>
        <Tab eventKey={3} disabled={!ADMIN} title="Fix Skew" className="full card">
          <div className="cardface">
            <Skew
            getUnlabeled={getUnlabeled}
            unlabeled_data={unlabeled_data}
            labels={labels}
            skewLabel={skewLabel}
            getLabelCounts={getLabelCounts}
            label_counts={label_counts}
            />
          </div>
        </Tab>
        <Tab eventKey={4} disabled={!ADMIN} title="Skipped Cards" className="full card">
          <div className="cardface">
            <AdminTable
            getAdmin={getAdmin}
            admin_data={admin_data}
            labels={labels}
            adminLabel={adminLabel}
            />
          </div>
        </Tab>
      </Tabs>
  );
}

Smart.propTypes = {
    cards: PropTypes.arrayOf(PropTypes.object),
    message: PropTypes.string,
    history_data: PropTypes.arrayOf(PropTypes.object),
    labels: PropTypes.arrayOf(PropTypes.object),
    label_counts: PropTypes.arrayOf(PropTypes.object),
    admin_data: PropTypes.arrayOf(PropTypes.object)
};

export default Smart;
