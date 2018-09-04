import React from 'react';
import PropTypes from 'prop-types';
import { Button, ButtonToolbar, Clearfix, Well, Tooltip, OverlayTrigger,
    Glyphicon, ProgressBar, Tabs, Tab, Badge } from "react-bootstrap";
import Card from '../Card';
import HistoryTable from '../HistoryTable';
import Skew from '../Skew';
import AdminTable from '../AdminTable';
import RecycleBinTable from '../RecycleBinTable';
import CodebookLabelMenu from '../CodebookLabelMenu';

const ADMIN = window.ADMIN;


class Smart extends React.Component {

    componentWillMount() {
        this.props.fetchCards();
        this.props.getAdminTabsAvailable();
        this.props.getAdminCounts();
    }

    renderAdminTabSkew() {
        let adminTabSkew;
        const { getUnlabeled, unlabeled_data, skewLabel, getLabelCounts,
            label_counts, labels, adminTabsAvailable } = this.props;

        if (adminTabsAvailable) {
            adminTabSkew = (
                <Tab eventKey={3} title="Fix Skew" className="full card">
                    <div className="cardContent">
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
            );
        } else {
            adminTabSkew = (
                <Tab eventKey={3} title="Fix Skew" className="full card">
                    <div className="cardContent">
                        <h2>Another admin is currently using this page. Please check back later.</h2>
                    </div>
                </Tab>
            );
        }

        return adminTabSkew;
    }

    renderAdminTabAdminTable() {
        let adminTabAdminTable, badges;
        const { getAdmin, admin_data, adminLabel, discardData, labels,
            adminTabsAvailable, admin_counts } = this.props;

        if (adminTabsAvailable) {
            if (Object.keys(admin_counts).length > 1) {
                badges = (
                    <div>
                        IRR
                        <Badge className="tab-badge">
                            {admin_counts["IRR"]}
                        </Badge>
                        | Skipped
                        <Badge className="tab-badge">
                            {admin_counts["SKIP"]}
                        </Badge>
                    </div>
                );
            } else {
                badges = (
                    <div>
                        Skipped
                        <Badge className="tab-badge">
                            {admin_counts["SKIP"]}
                        </Badge>
                    </div>
                );
            }

            adminTabAdminTable = (
                <Tab eventKey={4}
                    title={badges}
                    className="full card">
                    <div className="cardContent">
                        <AdminTable
                            getAdmin={getAdmin}
                            admin_data={admin_data}
                            labels={labels}
                            adminLabel={adminLabel}
                            discardData={discardData}
                        />
                    </div>
                </Tab>
            );
        } else {
            adminTabAdminTable = (
                <Tab eventKey={4} title="Skipped Cards" className="full card">
                    <div className="cardContent">
                        <h2>Another admin is currently using this page. Please check back later.</h2>
                    </div>
                </Tab>
            );
        }

        return adminTabAdminTable;
    }

    renderAdminTabRecycle() {
        let adminTabRecycle;
        const { getDiscarded, discarded_data, restoreData, labels, adminTabsAvailable } = this.props;

        if (adminTabsAvailable) {
            adminTabRecycle = (
                <Tab eventKey={5} title={<Glyphicon glyph="trash"/>} className="full card">
                    <div className="cardContent">
                        <RecycleBinTable
                            getDiscarded = {getDiscarded}
                            discarded_data = {discarded_data}
                            restoreData = {restoreData}
                            labels={labels}
                        />
                    </div>
                </Tab>
            );
        } else {
            adminTabRecycle = (
                <Tab eventKey={5} title={<Glyphicon glyph="trash"/>} className="full card">
                    <div className="cardContent">
                        <h2>Another admin is currently using this page. Please check back later.</h2>
                    </div>
                </Tab>
            );
        }

        return adminTabRecycle;
    }

    render() {
        let card;
        const { labels, message, cards, passCard, annotateCard, history_data, getHistory,
            changeLabel, changeToSkip } = this.props;

        let progress = 100;
        let start_card = 0;
        let num_cards = 0;
        let label = "Complete";
        if (!(cards === undefined) && cards.length > 0) {
            num_cards = cards[cards.length - 1].id + 1;
            start_card = cards[0].id + 1;
            progress = (cards[0].id / cards[cards.length - 1].id) * 100;
            label = start_card.toString() + " of " + num_cards.toString();
        }
        if (!(cards === undefined) && cards.length > 0) {
            //just get the labels from the cards
            card = (
                <Card className="full" key={cards[0].id}>
                    <h2>Card {cards[0].id + 1}</h2>
                    <p>
                        { cards[0].text['text'] }
                    </p>
                    <ButtonToolbar bsClass="btn-toolbar pull-right">
                        {labels.map( (opt) => (
                            <Button onClick={() => annotateCard(cards[0], opt['pk'], cards.length, ADMIN)}
                                bsStyle="primary"
                                key={`deck-button-${opt['name']}`}>{opt['name']}</Button>
                        ))}
                        <OverlayTrigger
                            placement = "top"
                            overlay={
                                <Tooltip id="skip_tooltip">
                  Clicking this button will send this document to an administrator for review
                                </Tooltip>
                            }>
                            <Button onClick={() => {
                                passCard(cards[0], cards.length, ADMIN);
                            }}
                            bsStyle="info">Skip</Button>
                        </OverlayTrigger>
                    </ButtonToolbar>
                    <Clearfix />
                </Card>);
        } else {
            let blankDeckMessage = (message) ? message : "No more data to label at this time. Please check back later";
            card = (
                <Well bsSize="large">
                    { blankDeckMessage }
                </Well>
            );
        }

        return (
            <Tabs defaultActiveKey={1} id="data_tabs" >
                <Tab eventKey={1} title="Annotate Data" className="full card">
                    <div className="cardContent">
                        <CodebookLabelMenu labels={labels} />
                        <ProgressBar>
                            <ProgressBar
                                style={{ minWidth: 60 }}
                                label={label}
                                now={progress}/>
                        </ProgressBar>
                        {card}
                    </div>
                </Tab>
                <Tab eventKey={2} title="History" className="full card">
                    <div className="cardContent">
                        <HistoryTable
                            getHistory={getHistory}
                            history_data={history_data}
                            labels={labels}
                            changeLabel={changeLabel}
                            changeToSkip={changeToSkip}
                        />
                    </div>
                </Tab>
                { ADMIN === true && this.renderAdminTabSkew() }
                { ADMIN === true && this.renderAdminTabAdminTable() }
                { ADMIN === true && this.renderAdminTabRecycle() }
            </Tabs>
        );

    }
}
Smart.propTypes = {
    cards: PropTypes.arrayOf(PropTypes.object),
    message: PropTypes.string,
    history_data: PropTypes.arrayOf(PropTypes.object),
    getHistory: PropTypes.func.isRequired,
    changeLabel: PropTypes.func.isRequired,
    changeToSkip: PropTypes.func.isRequired,
    getUnlabeled: PropTypes.func.isRequired,
    unlabeled_data: PropTypes.arrayOf(PropTypes.object),
    adminTabsAvailable: PropTypes.bool,
    getAdminTabsAvailable: PropTypes.func.isRequired,
    label_counts: PropTypes.arrayOf(PropTypes.object),
    skewLabel: PropTypes.func.isRequired,
    getLabelCounts: PropTypes.func.isRequired,
    getAdmin: PropTypes.func.isRequired,
    admin_data: PropTypes.arrayOf(PropTypes.object),
    adminLabel: PropTypes.func.isRequired,
    discardData: PropTypes.func.isRequired,
    restoreData: PropTypes.func.isRequired,
    getDiscarded: PropTypes.func.isRequired,
    discarded_data: PropTypes.arrayOf(PropTypes.object),
    fetchCards: PropTypes.func.isRequired,
    annotateCard: PropTypes.func.isRequired,
    passCard: PropTypes.func.isRequired,
    popCard: PropTypes.func.isRequired,
    admin_counts: PropTypes.arrayOf(PropTypes.object),
    getAdminCounts: PropTypes.func.isRequired
};

export default Smart;
