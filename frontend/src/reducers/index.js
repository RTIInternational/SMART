import { combineReducers } from 'redux';

import classifier from './classifier';
import history from './history';

export default combineReducers({
    classifier,
    history
});
