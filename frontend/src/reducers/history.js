import { handleActions } from 'redux-actions';
import update from 'immutability-helper';

import { SET_HIST_DATA } from '../actions/history'

const initialState = {
    history_data: [],
    labels: []
};

const history = handleActions({
  [SET_HIST_DATA]: (state, action) => {
    return update(state, {history_data: { $set: [action.payload] } } )
  }
}, initialState);

export default history;
