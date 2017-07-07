import React from 'react';

import Header from '../Header';

const Wrapper = (props) => (
    <div>
        <Header />
        <main>
            {props.children}
        </main>
    </div>
);

export default Wrapper;