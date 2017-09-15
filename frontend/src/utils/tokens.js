const SMART_TOKEN = 'smart-token';

export const token = window.sessionStorage.getItem(SMART_TOKEN);

const extractToken = (state) => state.auth.token;

export const handleChange = (store) => {
    let previousToken = token;
    let currentToken = extractToken(store.getState());

    if (currentToken && previousToken !== currentToken) {
        window.sessionStorage.setItem(SMART_TOKEN, currentToken);
    }
    else if (!currentToken) {
        window.sessionStorage.removeItem(SMART_TOKEN);
    }
};
