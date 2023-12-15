import { createAction } from 'redux-actions';
import 'whatwg-fetch';

import { getConfig } from '../utils/fetch_configs';

export const SET_AVAILABLE = 'SET_AVAILABLE';
export const SET_LABEL = 'SET_LABEL';


export const set_available = createAction(SET_AVAILABLE);
export const setLabel = createAction(SET_LABEL);

//check if another admin is already using the admin tabs
export const getAdminTabsAvailable = (projectID) => {
    let apiURL = `/api/check_admin_in_progress/${projectID}/`;
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
                if (response.available == 0) {
                    dispatch(set_available(false));
                } else {
                    dispatch(set_available(true));
                }

            })
            .catch(err => console.log("Error: ", err));
    };
};

// Get the set of labels for the project
export const getLabels = (projectID) => {
    let apiURL = `/api/get_labels/${projectID}/`;
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
                dispatch(setLabel(response.labels));
            })
            .catch(err => console.log("Error: ", err));
    };
};
