import { createAction } from 'redux-actions';
import 'whatwg-fetch';

import { getConfig, postConfig } from '../utils/fetch_configs';
import { getAdmin } from './adminTables';
import { getLabelCounts } from './skew';

import { queryClient } from '../store';

export const SET_HIST_DATA = 'SET_HIST_DATA';
export const SET_UNLABELED = 'SET_UNLABELED';
export const SET_NUM_PAGES = 'SET_NUM_PAGES';
export const SET_CURRENT_PAGE = 'SET_CURRENT_PAGE';
export const SET_FILTER_CHOICES = 'SET_FILTER_CHOICES';
export const SET_METADATA_FIELDS = 'SET_METADATA_FIELDS';

export const set_num_pages = createAction(SET_NUM_PAGES);
export const set_hist_data = createAction(SET_HIST_DATA);
export const set_unlabeled = createAction(SET_UNLABELED);
export const set_current_page = createAction(SET_CURRENT_PAGE);
export const set_filter_choices = createAction(SET_FILTER_CHOICES);
export const set_metadata_fields = createAction(SET_METADATA_FIELDS);


export const toggleUnlabeled = (projectID) => {
    return (dispatch, getState) => {
        dispatch(set_unlabeled(!getState().history.unlabeled));
        dispatch(set_current_page(1));
        dispatch(getHistory(projectID));
    };
};


export const setCurrentPage = (projectID, page, getHist) => {
    return (dispatch) => {
        dispatch(set_current_page(page));
        if (getHist) {
            dispatch(getHistory(projectID));
        }
    };
};


export const filterHistoryTable = (projectID, temp_filters) => {
    return (dispatch) => {
        dispatch(set_filter_choices(temp_filters));
        dispatch(getHistory(projectID));
    };
};

//Get the data for the history table
export const getHistory = (projectID) => {
    return (dispatch, getState) => {
        let params = {
            unlabeled: getState().history.unlabeled,
            current_page: getState().history.current_page,
        };
        let current_filters = getState().history.filter_choices;
        for (const [key, value] of Object.entries(current_filters)) {
            params[key] = value;
        }
        params = new URLSearchParams(params);
        let apiURL = `/api/get_label_history/${projectID}/?${params.toString()}`;
        return fetch(apiURL, getConfig())
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else {
                    const error = new Error(response.statusText);
                    error.response = response;
                    throw error;
                }
            })
            .then(response => {
                // If error was in the response then set that message
                let all_data = [];
                for (let i = 0; i < response.data.length; i++) {
                    const row = {
                        id: response.data[i].id,
                        pk: response.data[i].pk,
                        data: response.data[i].data,
                        metadata: response.data[i].metadata,
                        formattedMetadata: response.data[i].formattedMetadata,
                        metadataIDs: response.data[i].metadataIDs,
                        current_label: response.data[i].label,
                        current_label_id: response.data[i].labelID,
                        timestamp: response.data[i].timestamp,
                        verified: response.data[i].verified,
                        verified_by:response.data[i].verified_by,
                        pre_loaded: response.data[i].pre_loaded,
                        edit: response.data[i].edit,
                        project: projectID,
                        profile: response.data[i].profile
                    };
                    all_data.push(row);
                }
                dispatch(set_hist_data(all_data));
                dispatch(set_num_pages(response.total_pages));
                dispatch(set_metadata_fields(response.metadata_fields));
            })
            .catch(err => console.log("Error: ", err));
    };
};


export const changeLabel = (dataID, oldLabelID, labelID, projectID) => {
    let payload = {
        dataID: dataID,
        oldLabelID: oldLabelID,
        labelID: labelID
    };
    let apiURL = `/api/modify_label/${dataID}/`;
    return dispatch => {
        return fetch(apiURL, postConfig(payload))
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else {
                    const error = new Error(response.statusText);
                    error.response = response;
                    throw error;
                }
            })
            .then(() => {
                dispatch(getHistory(projectID));
                dispatch(getLabelCounts(projectID));
            });
    };
};

export const changeToSkip = (dataID, oldLabelID, projectID, message) => {
    let payload = {
        dataID: dataID,
        message,
        oldLabelID: oldLabelID,
    };
    let apiURL = `/api/modify_label_to_skip/${dataID}/`;
    return dispatch => {
        return fetch(apiURL, postConfig(payload))
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else {
                    const error = new Error(response.statusText);
                    error.response = response;
                    throw error;
                }
            })
            .then(() => {
                dispatch(getHistory(projectID));
                dispatch(getAdmin(projectID));
                queryClient.invalidateQueries(["adminCounts", projectID]);

            });
    };
};


export const verifyDataLabel = (dataID, projectID) => {
    let payload = {
        dataID: dataID
    };
    let apiURL = `/api/verify_label/${dataID}/`;
    return dispatch => {
        return fetch(apiURL, postConfig(payload))
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else {
                    const error = new Error(response.statusText);
                    error.response = response;
                    throw error;
                }
            }).then(() => {
                dispatch(getHistory(projectID));
            });
    };
};
