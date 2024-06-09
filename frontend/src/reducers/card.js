import { handleActions } from 'redux-actions';
import update from 'immutability-helper';
import moment from 'moment';

import { REMOVE_CARD, PUSH_CARD, SET_MESSAGE, CLEAR_DECK } from '../actions/card';

const initialState = {
    cards: [],
    message: ''
};

const card = handleActions({
    [REMOVE_CARD]: (state, action) => {
        let indexToRemove = -1;
        for (let i = 0; i < state.cards.length; i++) {
            if (state.cards[i].text.pk == action.payload) {
                indexToRemove = i; 
                break;
            }
        }
        if (indexToRemove === -1) {
            return state; 
        }
        const newState = update(state, { cards: { $splice: [[indexToRemove, 1]] } });
        if (newState.cards.length > 0) {
            newState.cards[0].start_time = moment();
        }
        return newState;
    },
    [PUSH_CARD]: (state, action) => {
        // Set the start time of the new top card to the current time
        for (let i = 0; i < state.cards.length; i++) {
            if (state.cards[i].id == action.payload.id) {
                return state;
            }
        }
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
