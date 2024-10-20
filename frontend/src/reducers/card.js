import { handleActions } from 'redux-actions';
import update from 'immutability-helper';
import moment from 'moment';

import { POP_CARD, PUSH_CARD, SET_MESSAGE, CLEAR_DECK } from '../actions/card';

const initialState = {
    cards: [],
    message: ''
};

const card = handleActions({
    [POP_CARD]: (state, action) => {
        // if the card isn't the first item in the deck don't pop it off
        // This handles double-clicking of Skip
        if (state.cards[0].text.pk != action.payload) {
            return state;
        }

        // Set the start time of the new top card to the current time
        if (state.cards.length > 1) {
            state.cards[1]['start_time'] = moment();
        }
        return update(state, { cards: { $splice: [[0, 1]] } } );
    },
    [PUSH_CARD]: (state, action) => {
        // only push the card if it's not already in the stack - failsafe
        for (let i = 0; i < state.cards.length; i++) {
            if (state.cards[i].id == action.payload.id) {
                return state;
            }
        }
        // Set the start time of the new top card to the current time
        if (state.cards.length > 0) {
            state.cards[0]['start_time'] = moment();
        }
        return update(state, { cards: { $push: [action.payload] } } );
    },
    [SET_MESSAGE]: (state, action) => (
        update(state, { message: { $set: [action.payload] } } )
    ),
    [CLEAR_DECK]: (state) => (
        update(state, { cards : { $set: [] } } )
    )
}, initialState);

export default card;
