import { createAction } from 'redux-actions';
import 'whatwg-fetch';

import { getConfig, postConfig } from '../utils/fetch_configs';
import { getAdminCounts } from './smart';
import { setMessage } from './card';
import { getHistory } from './history';
import { getUnlabeled, getLabelCounts } from './skew';
import { getDiscarded } from './recycleBin';

export const SET_ADMIN_DATA = 'SET_ADMIN_DATA';
export const SET_DISCARDED_DATA = 'SET_DISCARDED_DATA';

export const set_admin_data = createAction(SET_ADMIN_DATA);
export const set_discarded_data = createAction(SET_DISCARDED_DATA);

//get the skipped data for the admin Table
export const getAdmin = (projectID) => {
    let apiURL = `/api/data_admin_table/${projectID}/`;
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
                dispatch(set_admin_data(response.data));
            })
            .catch(err => console.log('Error: ', err));
    };
};

export const adminLabel = (dataID, labelID, labelReason, projectID) => {
    let payload = {
        labelID: labelID,
        labelReason: labelReason
    };
    let apiURL = `/api/label_admin_label/${dataID}/`;
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
                    return dispatch(setMessage(response.error));
                } else {
                    dispatch(getUnlabeled({ page: 1, filtered: [], sorted: [] }, projectID));
                    dispatch(getHistory(projectID));
                    dispatch(getLabelCounts(projectID));
                    dispatch(getAdmin(projectID));
                    dispatch(getAdminCounts(projectID));
                }
            });
    };
};

//mark data as uncodable and put it in the recycle bin
export const discardData = (dataID, projectID) => {
    let apiURL = `/api/discard_data/${dataID}/`;
    return dispatch => {
        return fetch(apiURL, postConfig())
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
                    return dispatch(setMessage(response.error));
                } else {
                    dispatch(getAdmin(projectID));
                    dispatch(getAdminCounts(projectID));
                    dispatch(getDiscarded(projectID));
                    dispatch(getUnlabeled({ page: 1, filtered: [], sorted: [] }, projectID));
                }
            });
    };
};
