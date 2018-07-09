import { handleActions } from 'redux-actions';
import update from 'immutability-helper';

import { SET_UNLABELED_DATA, SET_LABEL_COUNTS, SET_ADMIN_DATA } from '../actions/adminTables'

const initialState = {
    unlabeled_data: [],
    label_counts: []
};

const adminTables = handleActions({
  [SET_UNLABELED_DATA]: (state, action) => {
    return update(state, {unlabeled_data: { $set: [action.payload] } } )
  },
  [SET_LABEL_COUNTS]: (state, action) => {
    return update(state, {label_counts: { $set: [action.payload] } } )
  },
  [SET_ADMIN_DATA]: (state, action) => {
    return update(state, {admin_data: { $set: [action.payload] } } )
  }
}, initialState);

export default adminTables;
