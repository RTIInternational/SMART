import React from 'react';
import PropTypes from 'prop-types';
import { Tabs, Tab, Badge } from "react-bootstrap";
import CardContainer from '../../containers/card_container';
import HistoryContainer from '../../containers/history_container';
import SkewContainer from '../../containers/skew_container';
import AdminTableContainer from '../../containers/adminTable_container';
import RecycleBinContainer from '../../containers/recycleBin_container';
import CodebookLabelMenuContainer from '../../containers/codebookLabelMenu_container';
import SmartProgressBarContainer from '../../containers/smartProgressBar_container';


const ADMIN = window.ADMIN;

class Smart extends React.Component {

    componentDidMount() {
        this.props.getAdminTabsAvailable();
        this.props.getAdminCounts();
        this.props.getLabels();
    }

    renderAdminTabSkew() {
        let adminTabSkew;
        const { adminTabsAvailable } = this.props;

        if (adminTabsAvailable) {
            adminTabSkew = (
                <Tab eventKey={3} transition={false} title="Fix Skew" className="full card">
                    <div className="cardContent">
                        <SkewContainer />
                    </div>
                </Tab>
            );
        } else {
            adminTabSkew = (
                <Tab eventKey={3} transition={false} title="Fix Skew" className="full card">
                    <div className="cardContent">
                        <h2>Another admin is currently using this page. This page will become available when the admin returns to the project list page, details page, changes projects, or logs out.</h2>
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
                        | Requires Adjudication
                        <Badge className="tab-badge">
                            {admin_counts["SKIP"]}
                        </Badge>
                    </div>
                );
            } else {
                badges = (
                    <div>
                        Requires Adjudication
                        <Badge className="tab-badge">
                            {admin_counts["SKIP"]}
                        </Badge>
                    </div>
                );
            }

            adminTabAdminTable = (
                <Tab eventKey={4}
                    transition={false}
                    title={badges}
                    className="full card">
                    <div className="cardContent">
                        <AdminTableContainer />
                    </div>
                </Tab>
            );
        } else {
            adminTabAdminTable = (
                <Tab eventKey={4} transition={false} title="Requires Adjudication" className="full card">
                    <div className="cardContent">
                        <h2>Another admin is currently using this page. This page will become available when the admin returns to the project list page, details page, changes projects, or logs out.</h2>
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
                <Tab eventKey={5} transition={false} title={<div><span id="trashCan" className="glyphicon glyphicon-trash" aria-hidden="true"></span> Discarded Data</div>} className="full card">
                    <div className="cardContent">
                        <RecycleBinContainer />
                    </div>
                </Tab>
            );
        } else {
            adminTabRecycle = (
                <Tab eventKey={5} transition={false} title={<div><span id="trashCan" className="glyphicon glyphicon-trash" aria-hidden="true"></span> Discarded Data</div>} className="full card">
                    <div className="cardContent">
                        <h2>Another admin is currently using this page. This page will become available when the admin returns to the project list page, details page, changes projects, or logs out.</h2>
                    </div>
                </Tab>
            );
        }

        return adminTabRecycle;
    }

    render() {
        return (
            <Tabs defaultActiveKey={2} id="data_tabs" mountOnEnter={true} unmountOnExit={true}>
                <Tab eventKey={1} title="Annotate Data" className="full card" transition={false}>
                    <div className="cardContent">
                        <CodebookLabelMenuContainer />
                        <SmartProgressBarContainer />
                        <CardContainer />
                    </div>
                </Tab>
                <Tab eventKey={2} title="History" className="full card" transition={false}>
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
    adminTabsAvailable: PropTypes.bool,
    admin_counts: PropTypes.arrayOf(PropTypes.object),
    getAdminCounts: PropTypes.func.isRequired,
    getLabels: PropTypes.func.isRequired,
};

export default Smart;
