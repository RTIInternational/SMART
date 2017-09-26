import { createAction } from 'redux-actions';
import 'whatwg-fetch';

import { getConfig } from '../utils/fetch_configs';

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
    // Handle the case where the project has no queue
    // NOTE: This shouldnt happen because queues are created when project is created
    if (queueID == null) {
        return dispatch => {
            let message = 'There is no queue for this project.  Please have your administator add data to the project.';
            dispatch(setMessage(message));
        }
    }
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
                        text: response.data[i]
                    }
                    dispatch(pushCard(card));
                }
            })
            .catch(err => console.log("Error: ", err));
    }
};