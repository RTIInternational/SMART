import { createAction } from 'redux-actions';
import 'whatwg-fetch';

import { getConfig, postConfig } from '../utils/fetch_configs';
import { setMessage } from './card';
import { getHistory } from './history';

export const SET_UNLABELED_DATA = 'SET_UNLABELED_DATA';
export const SET_LABEL_COUNTS = 'SET_LABEL_COUNTS';
export const SET_SKEW_PAGES = 'SET_SKEW_PAGES';

export const set_unlabeled_data = createAction(SET_UNLABELED_DATA);
export const set_label_counts = createAction(SET_LABEL_COUNTS);
export const set_skew_pages = createAction(SET_SKEW_PAGES);

//Get the data for the skew table
export const getUnlabeled = (queryObj, projectID) => {

    let queryURLObj = new URLSearchParams("");

    queryURLObj.append("project", projectID);
    queryURLObj.append("page", queryObj.page + 1);

    if (queryObj.filtered.length > 0) {
        queryURLObj.append("text__icontains", queryObj.filtered[0].value);
    }

    if (queryObj.sorted.length > 0) {
        if (queryObj.sorted[0].desc) {
            queryURLObj.append("ordering", "text");
        } else {
            queryURLObj.append("ordering", "-text");
        }

    }


    let apiURL = `/api/data_unlabeled_table/?${queryURLObj.toString()}`;
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

                let data = [];
                for (let i = 0; i < response.results.length; i++) {
                    let row = {};
                    row["data"] = response.results[i]["text"];
                    row["id"] = response.results[i]["pk"];

                    if (response.results[i]["metadata"]) {
                        row["created_date"] = response.results[i]["metadata"]["created_date"];
                        row["title"] = response.results[i]["metadata"]["title"];
                        row["username"] = response.results[i]["metadata"]["username"];
                        row["url"] = response.results[i]["metadata"]["url"];
                        row["user_url"] = response.results[i]["metadata"]["user_url"];
                    } else {
                        row["created_date"] = null;
                        row["title"] = "";
                        row["username"] = "";
                        row["url"] = "";
                        row["user_url"] = "";
                    }

                    data.push(row);
                }

                dispatch(set_unlabeled_data(data));
                dispatch(set_skew_pages(Math.ceil(response.count / 20)));
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
                    dispatch(getUnlabeled({ page: 0, filtered: [], sorted:[] }, projectID));
                    dispatch(getHistory(projectID));
                    dispatch(getLabelCounts(projectID));
                }
            });
    };
};
