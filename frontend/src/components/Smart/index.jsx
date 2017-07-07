import React from 'react';

import Deck from '../Deck';
import Wrapper from '../Wrapper';

const Smart = ( props ) => (
    <Wrapper>
        <Deck {...props} />
    </Wrapper>
);

export default Smart;