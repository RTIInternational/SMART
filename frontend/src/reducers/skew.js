import { handleActions } from 'redux-actions';
import update from 'immutability-helper';

import { SET_UNLABELED_DATA, SET_LABEL_COUNTS, SET_SKEW_PAGES } from '../actions/skew';

const initialState = {
    unlabeled_data: [],
    label_counts: [],
    skew_pages: -1
};

const skew = handleActions({
    [SET_UNLABELED_DATA]: (state, action) => {
        return update(state, { unlabeled_data: { $set: action.payload } } );
    },
    [SET_LABEL_COUNTS]: (state, action) => {
        return update(state, { label_counts: { $set: action.payload } } );
    },
    [SET_SKEW_PAGES]: (state, action) => {
        return update(state, { skew_pages: { $set: action.payload } } );
    }
}, initialState);

export default skew;
