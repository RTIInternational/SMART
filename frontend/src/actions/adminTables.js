import { createAction } from 'redux-actions';
import 'whatwg-fetch';

import { getConfig, postConfig } from '../utils/fetch_configs';
import { setMessage } from './classifier';
import { getHistory } from './history';
export const SET_UNLABELED_DATA = 'SET_UNLABELED_DATA';
export const SET_LABEL_COUNTS = 'SET_LABEL_COUNTS';
export const SET_ADMIN_DATA = 'SET_ADMIN_DATA';
export const SET_DISCARDED_DATA = 'SET_DISCARDED_DATA';
export const SET_AVAILABLE = 'SET_AVAILABLE';
export const SET_ADMIN_COUNTS = 'SET_ADMIN_COUNTS';

export const set_unlabeled_data = createAction(SET_UNLABELED_DATA);
export const set_label_counts = createAction(SET_LABEL_COUNTS);
export const set_admin_data = createAction(SET_ADMIN_DATA);
export const set_discarded_data = createAction(SET_DISCARDED_DATA);
export const set_available = createAction(SET_AVAILABLE);
export const set_admin_counts = createAction(SET_ADMIN_COUNTS);

//check if another admin is already using the admin tabs
export const getAdminTabsAvailable = (projectID) => {
    let apiURL = `/api/check_admin_in_progress/${projectID}/`;
    return dispatch => {
        return fetch(apiURL, getConfig())
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else {
                    const error = new Error(response.statusText)
                    error.response = response;
                    throw error;
                }
            })
            .then(response => {
            // If error was in the response then set that message
                if ('error' in response) console.log(response);
                if(response.available == 0) {
                    dispatch(set_available(false));
                } else {
                    dispatch(set_available(true));
                }

            })
            .catch(err => console.log("Error: ", err));
    }
};

//Get the data for the skew table
export const getUnlabeled = (projectID) => {
    let apiURL = `/api/data_unlabeled_table/${projectID}/`;
    return dispatch => {
        return fetch(apiURL, getConfig())
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else {
                    const error = new Error(response.statusText)
                    error.response = response;
                    throw error;
                }
            })
            .then(response => {
            // If error was in the response then set that message
                if ('error' in response) console.log(response);
                var all_data = [];
                for (let i = 0; i < response.data.length; i++) {
                    const row = {
                        id: response.data[i].ID,
                        data: response.data[i].Text
                    }
                    all_data.push(row);
                }
                dispatch(set_unlabeled_data(all_data));
            })
            .catch(err => console.log("Error: ", err));
    }
};

export const skewLabel = (dataID, labelID, projectID) => {
    let payload = {
        labelID: labelID,
        labeleing_time: null
    }
    let apiURL = `/api/label_skew_label/${dataID}/`;
    return dispatch => {
        return fetch(apiURL, postConfig(payload))
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else {
                    const error = new Error(response.statusText)
                    error.response = response;
                    throw error;
                }
            })
            .then(response => {
                if ('error' in response) {
                    return dispatch(setMessage(response.error))
                } else {
                    dispatch(getUnlabeled(projectID))
                    dispatch(getHistory(projectID))
                    dispatch(getLabelCounts(projectID))
                }
            })
    }
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
                    const error = new Error(response.statusText)
                    error.response = response;
                    throw error;
                }
            })
            .then(response => {
            // If error was in the response then set that message
                if ('error' in response) console.log(response);
                dispatch(set_label_counts(response));
            })
            .catch(err => console.log("Error: ", err));
    }
};

//get the skipped data for the admin Table
export const getAdmin = (projectID) => {
    let apiURL = `/api/data_admin_table/${projectID}/`;
    return dispatch => {
        return fetch(apiURL, getConfig())
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else {
                    const error = new Error(response.statusText)
                    error.response = response;
                    throw error;
                }
            })
            .then(response => {
            // If error was in the response then set that message
                if ('error' in response) console.log(response);
                var all_data = [];
                for (let i = 0; i < response.data.length; i++) {
                    const row = {
                        id: response.data[i].ID,
                        data: response.data[i].Text,
                        reason: response.data[i].Reason
                    }
                    all_data.push(row);
                }
                dispatch(set_admin_data(all_data));
            })
            .catch(err => console.log("Error: ", err));
    }
};

//get the skipped data for the admin Table
export const getAdminCounts = (projectID) => {
    let apiURL = `/api/data_admin_counts/${projectID}/`;
    return dispatch => {
        return fetch(apiURL, getConfig())
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else {
                    const error = new Error(response.statusText)
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
    }
};

export const adminLabel = (dataID, labelID, projectID) => {
    let payload = {
        labelID: labelID,
    }
    let apiURL = `/api/label_admin_label/${dataID}/`;
    return dispatch => {
        return fetch(apiURL, postConfig(payload))
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else {
                    const error = new Error(response.statusText)
                    error.response = response;
                    throw error;
                }
            })
            .then(response => {
                if ('error' in response) {
                    return dispatch(setMessage(response.error))
                } else {
                    dispatch(getUnlabeled(projectID))
                    dispatch(getHistory(projectID))
                    dispatch(getLabelCounts(projectID))
                    dispatch(getAdmin(projectID))
                    dispatch(getAdminCounts(projectID))
                }
            })
    }
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
                    const error = new Error(response.statusText)
                    error.response = response;
                    throw error;
                }
            })
            .then(response => {
                if ('error' in response) {
                    return dispatch(setMessage(response.error))
                } else {
                    dispatch(getAdmin(projectID))
                    dispatch(getAdminCounts(projectID))
                    dispatch(getDiscarded(projectID))
                    dispatch(getUnlabeled(projectID))
                }
            })
    }
};

//take data out of the recycle bin
export const restoreData = (dataID, projectID) => {
    let apiURL = `/api/restore_data/${dataID}/`;
    return dispatch => {
        return fetch(apiURL, postConfig())
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else {
                    const error = new Error(response.statusText)
                    error.response = response;
                    throw error;
                }
            })
            .then(response => {
                if ('error' in response) {
                    return dispatch(setMessage(response.error))
                } else {
                    dispatch(getDiscarded(projectID))
                    dispatch(getUnlabeled(projectID))
                }
            })
    }
};

//get the discarded data for the recycle bin table
export const getDiscarded = (projectID) => {
    let apiURL = `/api/recycle_bin_table/${projectID}/`;
    return dispatch => {
        return fetch(apiURL, getConfig())
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else {
                    const error = new Error(response.statusText)
                    error.response = response;
                    throw error;
                }
            })
            .then(response => {
            // If error was in the response then set that message
                if ('error' in response) console.log(response);
                var all_data = [];
                for (let i = 0; i < response.data.length; i++) {
                    const row = {
                        id: response.data[i].ID,
                        data: response.data[i].Text,
                    }
                    all_data.push(row);
                }
                dispatch(set_discarded_data(all_data));
            })
            .catch(err => console.log("Error: ", err));
    }
};
