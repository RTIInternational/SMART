import { combineReducers } from 'redux';

import smart from './smart';
import card from './card';
import history from './history';
import adminTables from './adminTables';
import skew from './skew';
import recycleBin from './recycleBin';

export default combineReducers({
    smart,
    card,
    history,
    skew,
    adminTables,
    recycleBin
});
