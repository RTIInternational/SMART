import { createAction } from 'redux-actions';
import 'whatwg-fetch';

import { getConfig, postConfig } from '../utils/fetch_configs';
import { setMessage } from './card';

export const SET_UNLABELED_DATA = 'SET_UNLABELED_DATA';
export const SET_LABEL_COUNTS = 'SET_LABEL_COUNTS';
export const SET_FILTER_STR = 'SET_FILTER_STR';

export const set_unlabeled_data = createAction(SET_UNLABELED_DATA);
export const set_label_counts = createAction(SET_LABEL_COUNTS);
export const set_filter_str = createAction(SET_FILTER_STR);


//Get the data for the skew table
export const getUnlabeled = (projectID) => {
    return (dispatch, getState) => {
        const filterStr = getState().skew.filter_str;
        const apiURL = `/api/data_unlabeled_table/${projectID}?text=${filterStr}`;
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
                if ('error' in response) console.log(response);
                let all_data = [];
                for (let i = 0; i < response.data.length; i++) {
                    const row = {
                        id: response.data[i].ID,
                        metadata: response.data[i].metadata,
                        data: response.data[i].Text,
                        project: projectID
                    };
                    all_data.push(row);
                }
                dispatch(set_unlabeled_data(all_data));
            })
            .catch(err => console.log("Error: ", err));
    };
};

//get the data for the skew graph
export const getLabelCounts = (projectID) => {
    let apiURL = `/api/label_distribution_inverted/${projectID}/`;
    return dispatch => {
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
                dispatch(set_label_counts(response));
            })
            .catch(err => console.log("Error: ", err));
    };
};

export const skewLabel = (dataID, labelID, projectID) => {
    let payload = {
        labelID: labelID,
        labeleing_time: null
    };
    let apiURL = `/api/label_skew_label/${dataID}/`;
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
            .then(response => {
                if ('error' in response) {
                    dispatch(setMessage(response.error));
                } else {
                    dispatch(getUnlabeled(projectID));
                    //dispatch(getLabelCounts(projectID));
                }
            });
    };
};

export const setFilterStr = (filterStr) => {
    return dispatch => {
        dispatch(set_filter_str(filterStr));
    };
};
