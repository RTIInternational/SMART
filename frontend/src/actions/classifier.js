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

// Get the labels from a project URL
export const getLabels = (projURL) => {
    return dispatch => {
        return fetch(projURL, getConfig())
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
            .then(data => {
                return data['labels']
            })
            .catch(err => console.log("Error: ", err));
    }
}


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
    else {
        let apiURL = `/api/queue/${queueID}/`;
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
                .then(data => {
                    // Make sure the queue is not empty
                    if (data.data.length === 0) {
                        let message = 'There is nothing in the queue.  Please check again later.';
                        return dispatch(setMessage(message));
                    }
                    // Now that we have queue data we still need the labels data from project
                    let labels = dispatch(getLabels(data['project'])).then(labels => {
                        // If the project has no labels then do not create cards
                        if (labels.length === 0) {
                            let message = 'There are no labels for this project. Please have your administator create labels.';
                            return dispatch(setMessage(message));
                        }
                        for (let i = 0; i < data.data.length; i++) {
                            const card = {
                                id: i,
                                options: labels,
                                text: data.data[i]
                            }
                            dispatch(pushCard(card));
                        }
                    })
                })
                .catch(err => console.log("Error: ", err));
        }
    }
};