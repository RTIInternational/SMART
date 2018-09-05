import React from 'react';
import PropTypes from 'prop-types';
import { Button, ButtonToolbar, Clearfix, Well, Tooltip, OverlayTrigger,
    Glyphicon, ProgressBar, Tabs, Tab, Badge } from "react-bootstrap";
import Card from '../Card';
import HistoryContainer from '../../containers/history_container';
import SkewContainer from '../../containers/skew_container';
import AdminTableContainer from '../../containers/adminTable_container';
import RecycleBinContainer from '../../containers/recycleBin_container';
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
        const { adminTabsAvailable } = this.props;

        if (adminTabsAvailable) {
            adminTabSkew = (
                <Tab eventKey={3} title="Fix Skew" className="full card">
                    <div className="cardContent">
                        <SkewContainer />
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
        const { adminTabsAvailable, admin_counts } = this.props;

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
                        <AdminTableContainer />
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
        const { adminTabsAvailable } = this.props;

        if (adminTabsAvailable) {
            adminTabRecycle = (
                <Tab eventKey={5} title={<Glyphicon glyph="trash"/>} className="full card">
                    <div className="cardContent">
                        <RecycleBinContainer />
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
        const { labels, message, cards, passCard, annotateCard } = this.props;

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
            <Tabs defaultActiveKey={1} id="data_tabs" mountOnEnter={true} unmountOnExit={true}>
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
                        <HistoryContainer />
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
    adminTabsAvailable: PropTypes.bool,
    getAdminTabsAvailable: PropTypes.func.isRequired,
    fetchCards: PropTypes.func.isRequired,
    annotateCard: PropTypes.func.isRequired,
    passCard: PropTypes.func.isRequired,
    popCard: PropTypes.func.isRequired,
    admin_counts: PropTypes.arrayOf(PropTypes.object),
    getAdminCounts: PropTypes.func.isRequired
};

export default Smart;
