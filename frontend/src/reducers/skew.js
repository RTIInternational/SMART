import { handleActions } from 'redux-actions';
import update from 'immutability-helper';

import { SET_UNLABELED_DATA, SET_LABEL_COUNTS, SET_FILTER_STR } from '../actions/skew';

const initialState = {
    unlabeled_data: [],
    label_counts: [],
    filter_str: "",
};

const skew = handleActions({
    [SET_UNLABELED_DATA]: (state, action) => {
        return update(state, { unlabeled_data: { $set: action.payload } } );
    },
    [SET_LABEL_COUNTS]: (state, action) => {
        return update(state, { label_counts: { $set: action.payload } } );
    },
    [SET_FILTER_STR]: (state, action) => {
        return update(state, { filter_str: { $set: action.payload } } );
    }
}, initialState);

export default skew;
