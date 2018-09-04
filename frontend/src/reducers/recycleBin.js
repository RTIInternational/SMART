import { handleActions } from 'redux-actions';
import update from 'immutability-helper';

import { SET_DISCARDED_DATA } from '../actions/recycleBin';

const initialState = {
    discarded_data: [],
};

const recycleBin = handleActions({
    [SET_DISCARDED_DATA]: (state, action) => {
        return update(state, { discarded_data: { $set: action.payload } } );
    }
}, initialState);

export default recycleBin;
