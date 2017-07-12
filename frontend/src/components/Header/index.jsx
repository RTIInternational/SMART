import React from 'react';

const Header = (props) => (
    <header>
        <a href="/"><h1>SMART</h1></a>
        {props.children}
    </header>
);

export default Header;
