import { handleActions } from 'redux-actions';
import update from 'immutability-helper';
import moment from 'moment';

import { PASS_CARD, POP_CARD, PUSH_CARD, SET_MESSAGE } from '../actions/classifier'

const initialState = {
    cards: [],
    message: ''
};

const classifier = handleActions({
    [PASS_CARD]: (state) => {
        // Pass on the first card by moving it to the end
        return update(state, { cards: { $apply: (arr) => {
            const elem0 = arr[0];
            // Set the start time of the new top card to the current time
            arr[1]['start_time'] = moment();
            let poppedArr = update(arr, { $splice: [[0, 1]] });
            return update(poppedArr, { $push: [elem0] });
        }}});
    },
    [POP_CARD]: (state) => {
        // Set the start time of the new top card to the current time
        if (state.cards.length > 1) {
            state.cards[1]['start_time'] = moment();
        }
        return update(state, { cards: { $splice: [[0, 1]] } } )
    },
    [PUSH_CARD]: (state, action) => {
        // Set the start time of the new top card to the current time
        if (state.cards.length > 0) {
            state.cards[0]['start_time'] = moment();
        }
        return update(state, { cards: { $push: [action.payload] } } )
    },
    [SET_MESSAGE]: (state, action) => (
        update(state, { message: { $set: [action.payload] } } )
    )
}, initialState);

export default classifier;
