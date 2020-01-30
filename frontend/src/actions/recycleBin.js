import { createAction } from 'redux-actions';
import 'whatwg-fetch';

import { getConfig, postConfig } from '../utils/fetch_configs';
import { setMessage } from './card';
import { getUnlabeled } from './skew';
import { getAdmin } from './adminTables';
import { getAdminCounts } from './smart';

export const SET_DISCARDED_DATA = 'SET_DISCARDED_DATA';


export const set_discarded_data = createAction(SET_DISCARDED_DATA);

//take data out of the recycle bin
export const restoreData = (dataID, projectID) => {
    let apiURL = `/api/restore_data/${dataID}/`;
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
                    dispatch(getDiscarded(projectID));
                    dispatch(getAdminCounts(projectID));
                    dispatch(getUnlabeled({ page: 1, filtered: [], sorted: [] }, projectID));
                }
            });
    };
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
                    const row = response.data[i];
                    if (row.explicit) {
                        row.explicit = "Yes";
                    } else {
                        row.explicit = "No";
                    }
                    all_data.push(row);
                }
                dispatch(set_discarded_data(all_data));
            })
            .catch(err => console.log("Error: ", err));
    };
};
