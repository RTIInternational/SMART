import { handleActions } from 'redux-actions';
import update from 'immutability-helper';

import { CLEAR_TOKEN, SET_TOKEN } from '../actions/auth'

const SMART_TOKEN = 'smart-token';

const initialState = {
    token: window.sessionStorage.getItem(SMART_TOKEN) || null
};

const auth = handleActions({
    [CLEAR_TOKEN]: (state) => {
        return update(state, { token: { $set: null } } )
    },
    [SET_TOKEN]: (state, action) => {
        return update(state, { token: { $set: action.payload } } )
    }
}, initialState);

export default auth;
