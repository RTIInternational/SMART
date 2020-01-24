import { createAction } from 'redux-actions';
import 'whatwg-fetch';

import { getConfig } from '../utils/fetch_configs';

export const SET_AVAILABLE = 'SET_AVAILABLE';
export const SET_ADMIN_COUNTS = 'SET_ADMIN_COUNTS';
export const SET_HAS_EXPLICIT = 'SET_HAS_EXPLICIT';

export const set_available = createAction(SET_AVAILABLE);
export const set_admin_counts = createAction(SET_ADMIN_COUNTS);
export const set_has_explicit = createAction(SET_HAS_EXPLICIT);

//get the counts that go on the adminTable tab badges
export const getAdminCounts = (projectID) => {
    let apiURL = `/api/data_admin_counts/${projectID}/`;
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
                dispatch(set_admin_counts(response.data));
            })
            .catch(err => console.log("Error: ", err));
    };
};

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

// Check if this project marks things as explicit or not
export const getHasExplicit = (projectID) => {
    let apiURL = `/api/has_explicit_button/${projectID}/`;
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
                dispatch(set_has_explicit(response.explicit_ind));
            })
            .catch(err => console.log("Error: ", err));
    };
};
