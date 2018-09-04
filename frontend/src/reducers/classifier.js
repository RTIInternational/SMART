import { handleActions } from 'redux-actions';
import update from 'immutability-helper';
import moment from 'moment';

import { POP_CARD, PUSH_CARD, SET_LABEL, SET_MESSAGE, CLEAR_DECK, SET_AVAILABLE, SET_ADMIN_COUNTS } from '../actions/classifier';

const initialState = {
    cards: [],
    message: '',
    labels: [],
    adminTabsAvailable: false,
    admin_counts: [],
};

const classifier = handleActions({
    [POP_CARD]: (state) => {
        // Set the start time of the new top card to the current time
        if (state.cards.length > 1) {
            state.cards[1]['start_time'] = moment();
        }
        return update(state, { cards: { $splice: [[0, 1]] } } );
    },
    [PUSH_CARD]: (state, action) => {
        // Set the start time of the new top card to the current time
        if (state.cards.length > 0) {
            state.cards[0]['start_time'] = moment();
        }
        return update(state, { cards: { $push: [action.payload] } } );
    },
    [SET_LABEL]: (state, action) => {
        // Set the start time of the new top card to the current time
        return update(state, { labels: { $set: action.payload } } );
    },
    [SET_MESSAGE]: (state, action) => (
        update(state, { message: { $set: [action.payload] } } )
    ),
    [CLEAR_DECK]: (state) => (
        update(state, { cards : { $set: [] } } )
    ),
    [SET_AVAILABLE]: (state, action) => {
        return update(state, { adminTabsAvailable: { $set: action.payload } } );
    },
    [SET_ADMIN_COUNTS]: (state, action) => {
        return update(state, { admin_counts: { $set: action.payload } } );
    }
}, initialState);

export default classifier;
