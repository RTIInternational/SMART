import React from 'react';
import ReactDOM from 'react-dom';

import { createStore, applyMiddleware, compose } from 'redux';
import { Provider } from 'react-redux';
import thunkMiddleware from 'redux-thunk';

import reducers from './reducers/index.js';
import SmartContainer from './containers/smart_container';

import './styles/smart.scss';

const composeEnhancers = window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__ || compose;
const store = createStore(reducers, composeEnhancers(
    applyMiddleware(thunkMiddleware)
));

console.log("SmartContainer::", SmartContainer);

ReactDOM.render(
    <Provider store={store}>
        <SmartContainer />
    </Provider>,
    document.getElementById('mount')
);
