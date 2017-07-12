import { combineReducers } from 'redux';

import auth from './auth';
import classifier from './classifier';

export default combineReducers({
    classifier,
    auth
});
