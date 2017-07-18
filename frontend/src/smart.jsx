import React from 'react';
import ReactDOM from 'react-dom';

import { createStore, applyMiddleware } from 'redux';
import { Provider } from 'react-redux';
import thunkMiddleware from 'redux-thunk';

import reducers from './reducers/index.js';
import { handleChange } from './utils/tokens';
import SmartContainer from './containers/smart_container';

import './styles/smart.scss';

const store = createStore(
    reducers,
    applyMiddleware(thunkMiddleware)
);

ReactDOM.render(
    <Provider store={store}>
        <SmartContainer />
    </Provider>,
    document.getElementById('mount')
);
