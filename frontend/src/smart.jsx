import "./styles/index.scss";
import "./styles/smart.scss";

import { QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import ReactDOM from "react-dom";

import { Provider } from "react-redux";
import { createStore, applyMiddleware, compose } from "redux";
import thunkMiddleware from "redux-thunk";

import SmartContainer from "./containers/smart_container";
import reducers from "./reducers/index.js";
import { queryClient } from "./store.js";

const composeEnhancers = window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__ || compose;
const store = createStore(reducers, composeEnhancers(
    applyMiddleware(thunkMiddleware)
));

ReactDOM.render(
    <QueryClientProvider client={queryClient}>
        <Provider store={store}>
            <SmartContainer />
        </Provider>
    </QueryClientProvider>,
    document.getElementById("mount")
);
