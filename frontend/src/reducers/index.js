import { combineReducers } from 'redux';

import classifier from './classifier';
import history from './history';
import adminTables from './adminTables';

export default combineReducers({
    classifier,
    history,
    adminTables
});
