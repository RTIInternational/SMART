import { handleActions } from 'redux-actions';
import update from 'immutability-helper';

import { SET_HIST_DATA, SET_UNLABELED_DATA } from '../actions/history';

const initialState = {
    history_data: [],
    unlabeled_data: []
};

const history = handleActions({
    [SET_HIST_DATA]: (state, action) => {
        return update(state, { history_data: { $set: action.payload } } );
    },
    [SET_UNLABELED_DATA]: (state, action) => {
        return update(state, { unlabeled_data: { $set: action.payload } });
    }
}, initialState);

export default history;
