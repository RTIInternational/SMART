import { createAction } from 'redux-actions';
import 'whatwg-fetch';

import { getConfig } from '../utils/fetch_configs';

export const PASS_CARD = 'PASS_CARD';
export const POP_CARD = 'POP_CARD';
export const PUSH_CARD = 'PUSH_CARD';

export const passCard = createAction(PASS_CARD);
export const popCard = createAction(POP_CARD);
export const pushCard = createAction(PUSH_CARD);

export const fetchCards = () => {
    return dispatch => {
        for (let i = 0; i < 12; i++) {
            const optionCount = Math.floor((Math.random() * 3) + 2);
            let options = [];
            for (let j = 0; j < optionCount; j++) {
                options.push(j + 1);
            }

            const card = {
                id: i,
                options: options
            };

            dispatch(pushCard(card));
        }
    };
};