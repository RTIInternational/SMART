import { handleActions } from 'redux-actions';
import update from 'immutability-helper';

import { SET_HIST_DATA, SET_UNLABELED } from '../actions/history';

const initialState = {
    history_data: [],
    unlabeled: false
};

const history = handleActions({
    [SET_HIST_DATA]: (state, action) => {
        return update(state, { history_data: { $set: action.payload } });
    },
    [SET_UNLABELED]: (state, action) => {
        return update(state, { unlabeled: { $set: action.payload } });
    }
}, initialState);

export default history;
