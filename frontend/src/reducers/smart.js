import { handleActions } from 'redux-actions';
import update from 'immutability-helper';

import { SET_AVAILABLE, SET_ADMIN_COUNTS, SET_HAS_EXPLICIT } from '../actions/smart';

const initialState = {
    adminTabsAvailable: false,
    hasExplicit: false,
    admin_counts: [],
};

const smart = handleActions({
    [SET_AVAILABLE]: (state, action) => {
        return update(state, { adminTabsAvailable: { $set: action.payload } } );
    },
    [SET_HAS_EXPLICIT]: (state, action) => {
        return update(state, { hasExplicit: { $set: action.payload } } );
    },
    [SET_ADMIN_COUNTS]: (state, action) => {
        return update(state, { admin_counts: { $set: action.payload } } );
    }
}, initialState);

export default smart;
