import { createAction } from 'redux-actions';
import 'whatwg-fetch';
import moment from 'moment';

import { getConfig, postConfig } from '../utils/fetch_configs';
import { getHistory } from './history';
import { getLabelCounts } from './adminTables';

export const POP_CARD = 'POP_CARD';
export const PUSH_CARD = 'PUSH_CARD';
export const SET_MESSAGE = 'SET_MESSAGE';
export const CLEAR_DECK = 'CLEAR_DECK';
export const SET_LABELS = 'SET_LABELS';

export const popCard = createAction(POP_CARD);
export const pushCard = createAction(PUSH_CARD);
export const setMessage = createAction(SET_MESSAGE);
export const clearDeck = createAction(CLEAR_DECK);
export const setLabels = createAction(SET_LABELS);

// Create cards by reading from a queue
export const fetchCards = (projectID) => {
    let apiURL = `/api/get_card_deck/${projectID}/`;
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

export const annotateCard = (card, labelID, projectID) => {
    let payload = {
        labelID: labelID,
        labeling_time: moment().diff(card['start_time'], 'seconds') // now - start_time rounded to whole seconds
    }
    let apiURL = `/api/annotate_data/${card.text.pk}/`;
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
                if ('error' in response) {
                    dispatch(clearDeck())
                    return dispatch(setMessage(response.error))
                }
                else {
                    dispatch(popCard())
                    dispatch(getHistory(projectID))
                    dispatch(getLabelCounts(projectID))
                }
            })
    }
}

//skip a card and put it in the admin table
export const passCard = (card) => {
    let payload = {
    }
    let apiURL = `/api/skip_data/${card.text.pk}/`;
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
                if ('error' in response) {
                    dispatch(clearDeck())
                    return dispatch(setMessage(response.error))
                }
                else {
                    dispatch(popCard())
                }
            })
    }
}
