import { handleActions } from 'redux-actions';
import update from 'immutability-helper';

import { SET_UNLABELED_DATA, SET_LABEL_COUNTS } from '../actions/skew';

const initialState = {
    unlabeled_data: [],
    label_counts: [],
};

const skew = handleActions({
    [SET_UNLABELED_DATA]: (state, action) => {
        return update(state, { unlabeled_data: { $set: action.payload } } );
    },
    [SET_LABEL_COUNTS]: (state, action) => {
        return update(state, { label_counts: { $set: action.payload } } );
    }
}, initialState);

export default skew;
