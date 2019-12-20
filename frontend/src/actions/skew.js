import { createAction } from 'redux-actions';
import 'whatwg-fetch';

import { getConfig, postConfig } from '../utils/fetch_configs';
import { setMessage } from './card';
import { getHistory } from './history';

export const SET_UNLABELED_DATA = 'SET_UNLABELED_DATA';
export const SET_LABEL_COUNTS = 'SET_LABEL_COUNTS';

export const set_unlabeled_data = createAction(SET_UNLABELED_DATA);
export const set_label_counts = createAction(SET_LABEL_COUNTS);

//Get the data for the skew table
export const getUnlabeled = (projectID) => {
    let apiURL = `/api/data_unlabeled_table/${projectID}/`;
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
                // If error was in the response then set that message
                if ('error' in response) console.log(response);
                let all_data = [];
                for (let i = 0; i < response.data.length; i++) {
                    const row = {
                        id: response.data[i].ID,
                        data: response.data[i].Text
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

export const skewLabel = (dataID, labelID, labelReason, projectID) => {
    let payload = {
        labelID: labelID,
        labeleing_time: null,
        labelReason: labelReason
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
                    dispatch(getHistory(projectID));
                    dispatch(getLabelCounts(projectID));
                }
            });
    };
};
