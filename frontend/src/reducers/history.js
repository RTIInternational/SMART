import { handleActions } from 'redux-actions';
import update from 'immutability-helper';

import { SET_HIST_DATA, SET_NUM_PAGES, SET_UNLABELED, SET_CURRENT_PAGE } from '../actions/history';

const initialState = {
    history_data: [],
    unlabeled: false,
    num_pages: 1,
    current_page: 1
};

const history = handleActions({
    [SET_HIST_DATA]: (state, action) => {
        return update(state, { history_data: { $set: action.payload } });
    },
    [SET_UNLABELED]: (state, action) => {
        return update(state, { unlabeled: { $set: action.payload } });
    },
    [SET_NUM_PAGES]: (state, action) => {
        return update(state, { num_pages: { $set: action.payload } });
    },
    [SET_CURRENT_PAGE]: (state, action) => {
        return update(state, { current_page: { $set: action.payload } });
    }
}, initialState);

export default history;
