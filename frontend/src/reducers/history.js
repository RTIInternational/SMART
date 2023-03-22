import { handleActions } from 'redux-actions';
import update from 'immutability-helper';

import { SET_HIST_DATA, SET_NUM_PAGES, SET_UNLABELED, SET_CURRENT_PAGE, SET_FILTER_CHOICES, SET_METADATA_FIELDS } from '../actions/history';

const initialState = {
    history_data: [],
    unlabeled: false,
    num_pages: 1,
    current_page: 1,
    metadata_fields: [],
    filter_choices: { text: "" }
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
    },
    [SET_FILTER_CHOICES]: (state, action) => {
        return update(state, { filter_choices: { $set: action.payload } });
    },
    [SET_METADATA_FIELDS]: (state, action) => {
        return update(state, { metadata_fields: { $set: action.payload } });
    }
}, initialState);

export default history;
