import { handleActions } from 'redux-actions';
import update from 'immutability-helper';

import { SET_ADMIN_DATA, SET_ADMIN_COUNTS, SET_IRR_LOG } from '../actions/adminTables';

const initialState = {
    admin_data: [],
    admin_counts: [],
    irr_log: []
};

const adminTables = handleActions({
    [SET_ADMIN_DATA]: (state, action) => {
        return update(state, { admin_data: { $set: action.payload } } );
    },
    [SET_IRR_LOG]: (state, action) => {
        return update(state, { irr_log: { $set: action.payload } } );
    },
    [SET_ADMIN_COUNTS]: (state, action) => {
        return update(state, { admin_counts: { $set: action.payload } } );
    }
}, initialState);

export default adminTables;
