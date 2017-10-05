import { createAction } from 'redux-actions';
import 'whatwg-fetch';

import { getConfig, postConfig } from '../utils/fetch_configs';

export const PASS_CARD = 'PASS_CARD';
export const POP_CARD = 'POP_CARD';
export const PUSH_CARD = 'PUSH_CARD';
export const SET_MESSAGE = 'SET_MESSAGE';

export const passCard = createAction(PASS_CARD);
export const popCard = createAction(POP_CARD);
export const pushCard = createAction(PUSH_CARD);
export const setMessage = createAction(SET_MESSAGE);


// Create cards by reading from a queue
export const fetchCards = (queueID) => {
    let apiURL = `/api/grab_from_queue/${queueID}/`;
    return dispatch => {
        return fetch(apiURL, getConfig())
            .then(response => {
                if (response.ok) {
                    return response.json();
                }
                else {
                    const error = new Error(response.statusText)
                    error.response = response;
                    throw error;
                }
            })
            .then(response => {
                // If error was in the response then set that message
                if ('error' in response) return dispatch(setMessage(response.error));

                for (let i = 0; i < response.data.length; i++) {
                    const card = {
                        id: i,
                        options: response.labels,
                        text: response.data[i],
                        queue_id: response.queue_id,
                    }
                    dispatch(pushCard(card));
                }
            })
            .catch(err => console.log("Error: ", err));
    }
};

export const annotateCard = (dataID, labelID, queueID) => {
    let payload = {
        labelID: labelID,
        queueID: queueID,
    }
    let apiURL = `/api/annotate_data/${dataID}/`;
    return dispatch => {
        return fetch(apiURL, postConfig(payload))
            .then(response => {
                if (response.ok) {
                    return response.json();
                }
                else {
                    const error = new Error(response.statusText)
                    error.response = response;
                    throw error;
                }
            })
            .then(response => {
                dispatch(popCard())
            })
    }
}