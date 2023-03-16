import React from 'react';
import { connect } from 'react-redux';

import { 
    getHistory, 
    changeLabel, 
    changeToSkip, 
    verifyDataLabel, 
    modifyMetadataValue, 
    toggleUnlabeled,
    setCurrentPage,
    filterHistoryTable
} from '../actions/history';
import History from '../components/History';

const PROJECT_ID = window.PROJECT_ID;

const HistoryContainer = (props) => <History {...props} />;

const mapStateToProps = (state) => {
    return {
        history_data: state.history.history_data,
        unlabeled: state.history.unlabeled,
        labels: state.card.labels,
        num_pages: state.history.num_pages,
        current_page: state.history.current_page,
        filterChoices: state.history.filter_choices,
        metadata_fields: state.history.metadata_fields
    };
};

const mapDispatchToProps = (dispatch) => {
    return {
        getHistory: () => {
            dispatch(getHistory(PROJECT_ID));
        },
        toggleUnlabeled: () => {
            dispatch(toggleUnlabeled(PROJECT_ID));
        },
        setCurrentPage: (page) => {
            dispatch(setCurrentPage(PROJECT_ID, page));
        },
        filterHistoryTable: (filter_choices) => {
            dispatch(filterHistoryTable(PROJECT_ID, filter_choices));
        },
        changeLabel: (dataID, oldLabelID, labelID) => {
            dispatch(changeLabel(dataID, oldLabelID, labelID, PROJECT_ID));
        },
        changeToSkip: (dataID, oldLabelID, message) => {
            dispatch(changeToSkip(dataID, oldLabelID, PROJECT_ID, message));
        },
        verifyDataLabel: (dataID) => {
            dispatch(verifyDataLabel(dataID, PROJECT_ID));
        },
        modifyMetadataValue: (metadataId, value) => {
            dispatch(modifyMetadataValue(metadataId, value));
        }
    };
};

export default connect(mapStateToProps, mapDispatchToProps)(HistoryContainer);
