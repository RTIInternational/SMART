import { handleActions } from 'redux-actions';
import update from 'immutability-helper';

import { SET_HIST_DATA, SET_LABELS} from '../actions/history'

const initialState = {
    history_data: [],
    labels: []
};

const history = handleActions({
  [SET_HIST_DATA]: (state, action) => {
    return update(state, {history_data: { $set: [action.payload] } } )
  },
  [SET_LABELS]: (state, action) => {
    return update(state, {labels: { $set: [action.payload] } } )
  }
}, initialState);

export default history;
