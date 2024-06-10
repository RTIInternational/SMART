import { createAction } from 'redux-actions';
import 'whatwg-fetch';
import moment from 'moment';

import { getConfig, postConfig } from '../utils/fetch_configs';
import { getAdmin } from './adminTables';
import { getLabelCounts, getUnlabeled } from './skew';

import { queryClient } from "../store";

export const POP_CARD = 'POP_CARD';
export const PUSH_CARD = 'PUSH_CARD';

export const SET_MESSAGE = 'SET_MESSAGE';
export const CLEAR_DECK = 'CLEAR_DECK';

export const popCard = createAction(POP_CARD);
export const pushCard = createAction(PUSH_CARD);
export const setMessage = createAction(SET_MESSAGE);
export const clearDeck = createAction(CLEAR_DECK);

// Create cards by reading from a queue
export const fetchCards = (projectID) => {
    let apiURL = `/api/get_card_deck/${projectID}/`;
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
                if ('error' in response) return dispatch(setMessage(response.error));
                for (let i = 0; i < response.data.length; i++) {
                    const card = {
                        id: i,
                        text: response.data[i]
                    };
                    dispatch(pushCard(card));
                }
            })
            .catch(err => console.log("Error: ", err));
    };
};

export const annotateCard = (dataID, labelID, num_cards_left, start_time, projectID, is_admin) => {
    let payload = {
        labelID: labelID,
        labeling_time: moment().diff(start_time, 'seconds') // now - start_time rounded to whole seconds
    };
    let apiURL = `/api/annotate_data/${dataID}/`;
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
                    dispatch(clearDeck());
                    return dispatch(setMessage(response.error));
                } else {
                    dispatch(popCard(dataID));
                    if (is_admin) {
                        dispatch(getAdmin(projectID));
                        queryClient.invalidateQueries(["adminCounts", projectID]);
                        dispatch(getLabelCounts(projectID));
                    }
                }
            });
    };
};

//unassign a card
export const unassignCard = (dataID, num_cards_left, is_admin, projectID) => {
    let apiURL = `/api/unassign_data/${dataID}/`;
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
                    dispatch(clearDeck());
                    return dispatch(setMessage(response.error));
                } else {
                    dispatch(popCard(dataID));
                }
            });
    };
};

//skip a card and put it in the admin table
export const passCard = (dataID, num_cards_left, is_admin, projectID, message) => {
    let apiURL = `/api/skip_data/${dataID}/`;
    return dispatch => {
        return fetch(apiURL, postConfig({ message }))
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
                    dispatch(clearDeck());
                    return dispatch(setMessage(response.error));
                } else {
                    dispatch(popCard(dataID));
                    if (is_admin) {
                        dispatch(getAdmin(projectID));
                        queryClient.invalidateQueries(["adminCounts", projectID]);
                    }
                }
            });
    };
};

// update a card's metadata
export const modifyMetadataValues = (dataPk, metadatas, projectPk) => {
    let apiURL = `/api/modify_metadata_values/${dataPk}/`;
    return dispatch => {
        return fetch(apiURL, postConfig({ metadatas }))
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else {
                    const error = new Error(response.statusText);
                    error.response = response;
                    throw error;
                }
            })
            .then(() => {
                dispatch(getUnlabeled(projectPk));
            });
    };
};
