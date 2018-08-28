import { handleActions } from 'redux-actions';
import update from 'immutability-helper';

import { SET_UNLABELED_DATA, SET_LABEL_COUNTS, SET_ADMIN_DATA, SET_DISCARDED_DATA, SET_AVAILABLE, SET_ADMIN_COUNTS } from '../actions/adminTables'

const initialState = {
    unlabeled_data: [],
    label_counts: [],
    discarded_data: [],
    available: false,
    admin_counts: []
};

const adminTables = handleActions({
    [SET_UNLABELED_DATA]: (state, action) => {
        return update(state, {unlabeled_data: { $set: action.payload } } )
    },
    [SET_LABEL_COUNTS]: (state, action) => {
        return update(state, {label_counts: { $set: action.payload } } )
    },
    [SET_ADMIN_DATA]: (state, action) => {
        return update(state, {admin_data: { $set: action.payload } } )
    },
    [SET_DISCARDED_DATA]: (state, action) => {
        return update(state, {discarded_data: { $set: action.payload } } )
    },
    [SET_AVAILABLE]: (state, action) => {
        return update(state, {available: { $set: action.payload } } )
    },
    [SET_ADMIN_COUNTS]: (state, action) => {
        return update(state, {admin_counts: { $set: action.payload } } )
    }
}, initialState);

export default adminTables;
