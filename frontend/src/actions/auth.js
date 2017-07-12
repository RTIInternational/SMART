import { createAction } from 'redux-actions';

const SMART_TOKEN = 'smart-token';

export const CLEAR_TOKEN = 'CLEAR_TOKEN';
export const SET_TOKEN = 'SET_TOKEN';

export const clearToken = createAction(CLEAR_TOKEN);
export const setToken = createAction(SET_TOKEN);

const api = (url, options = {}) => {
    return new Promise((resolve, reject) => {
        fetch(url, options)
            .then(response => {
                if (response.ok) {
                    return resolve(response.json());
                } else {
                    return reject(response.status, response.json());
                }
            });
    });
};

const error = (err) => {
    console.log("Error: ", err);
};

export const login = (data) => {
    const url = '/rest-auth/login/'
    
    const config = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify(data)
    };

    return dispatch => {
        api(url, config)
            .then(data => {
                window.sessionStorage.setItem(SMART_TOKEN, data.token);
                dispatch(setToken(data.token));
            })
            .catch(err => {
                error(err);
                window.sessionStorage.removeItem(SMART_TOKEN);
                dispatch(clearToken);
            });
    };
};

export const logout = (data) => {
    const url = '/rest-auth/logout/'
    
    const config = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authentication': `JWT ${window.sessionStorage.getItem(SMART_TOKEN)}`
        }
    };

    return dispatch => {
        api(url, config)
            .then(data => {
                dispatch(clearToken);
                window.sessionStorage.removeItem(SMART_TOKEN);
                window.location.reload();
            })
            .catch(err => error(err));
    };
};
