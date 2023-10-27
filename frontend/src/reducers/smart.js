import { handleActions } from 'redux-actions';
import update from 'immutability-helper';

import { SET_AVAILABLE, SET_ADMIN_COUNTS, SET_LABEL } from '../actions/smart';

const initialState = {
    adminTabsAvailable: false,
    admin_counts: [],
    labels: []
};

const smart = handleActions({
    [SET_AVAILABLE]: (state, action) => {
        return update(state, { adminTabsAvailable: { $set: action.payload } } );
    },
    [SET_ADMIN_COUNTS]: (state, action) => {
        return update(state, { admin_counts: { $set: action.payload } } );
    },
    [SET_LABEL]: (state, action) => {
        // Set the start time of the new top card to the current time
        return update(state, { labels: { $set: action.payload } } );
    }
}, initialState);

export default smart;
