import { handleActions } from 'redux-actions';
import update from 'immutability-helper';

import { SET_ADMIN_DATA, SET_DISCARDED_DATA, SET_AVAILABLE, SET_ADMIN_COUNTS } from '../actions/adminTables';

const initialState = {
    admin_data: [],
    discarded_data: [],
    adminTabsAvailable: false,
    admin_counts: []
};

const adminTables = handleActions({
    [SET_ADMIN_DATA]: (state, action) => {
        return update(state, { admin_data: { $set: action.payload } } );
    },
    [SET_DISCARDED_DATA]: (state, action) => {
        return update(state, { discarded_data: { $set: action.payload } } );
    },
    [SET_AVAILABLE]: (state, action) => {
        return update(state, { adminTabsAvailable: { $set: action.payload } } );
    },
    [SET_ADMIN_COUNTS]: (state, action) => {
        return update(state, { admin_counts: { $set: action.payload } } );
    }
}, initialState);

export default adminTables;
