import React from 'react';
import ReactDOM from 'react-dom';

import { createStore } from 'redux';
import { Provider } from 'react-redux';
import thunkMiddleware from 'redux-thunk';

import reducers from './reducers/index.js';

import Smart from './components/smart.jsx';

const store = createStore(
    reducers,
    thunkMiddleware
);

ReactDOM.render(
    <Provider store={store}>
        <Smart />
    </Provider>,
    document.getElementById('mount')
);