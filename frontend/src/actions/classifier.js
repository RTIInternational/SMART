import { createAction } from 'redux-actions';
import 'whatwg-fetch';

import { getConfig } from '../utils/fetch_configs';

export const PASS_CARD = 'PASS_CARD';
export const POP_CARD = 'POP_CARD';
export const PUSH_CARD = 'PUSH_CARD';

export const passCard = createAction(PASS_CARD);
export const popCard = createAction(POP_CARD);
export const pushCard = createAction(PUSH_CARD);

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

export const fetchCards = (queueID) => {
    if (queueID == null) { return dispatch => {} }
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
                    let labels = dispatch(getLabels(data['project'])).then(labels => {
                        for (let i = 0; i < data.length; i++) {
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