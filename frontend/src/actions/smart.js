import { createAction } from 'redux-actions';
import 'whatwg-fetch';

import { getConfig } from '../utils/fetch_configs';

export const SET_AVAILABLE = 'SET_AVAILABLE';

export const set_available = createAction(SET_AVAILABLE);

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

