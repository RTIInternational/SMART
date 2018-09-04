import { combineReducers } from 'redux';

import classifier from './classifier';
import history from './history';
import adminTables from './adminTables';
import skew from './skew';

export default combineReducers({
    classifier,
    history,
    skew,
    adminTables
});
