import React from 'react';
import ReactDOM from 'react-dom';

import { createStore, applyMiddleware } from 'redux';
import { Provider } from 'react-redux';
import thunkMiddleware from 'redux-thunk';

import reducers from './reducers/index.js';

import Smart from './components/smart';

import './styles/smart.scss';

const store = createStore(
    reducers,
    applyMiddleware(thunkMiddleware)
);

const Store = createStore(reducers);

ReactDOM.render(
    <Provider store={store}>
        <Smart />
    </Provider>,
    document.getElementById('mount')
);