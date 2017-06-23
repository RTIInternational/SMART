import { handleActions } from 'redux-actions';
import update from 'immutability-helper';

import { PASS_CARD, POP_CARD, PUSH_CARD } from '../actions/classifier'

const initialState = {
    cards: []
};

const classifier = handleActions({
    [PASS_CARD]: (state) => {
        // Pass on the first card by moving it to the end
        return update(state, { cards: { $apply: (arr) => {
            const elem0 = arr[0];
            let poppedArr = update(arr, { $splice: [[0, 1]] });
            return update(poppedArr, { $push: [elem0] });
        }}});
    },
    [POP_CARD]: (state) => (
        update(state, { cards: { $splice: [[0, 1]] } } )
    ),
    [PUSH_CARD]: (state, action) => (
        update(state, { cards: { $push: [action.payload] } } )
    )
}, initialState);

export default classifier;