import React from 'react';
import PropTypes from 'prop-types';

const Header = (props) => (
    <header>
        <a href="/"><h1>SMART</h1></a>
        {props.children}
    </header>
);

Header.propTypes = {
    children: PropTypes.oneOfType([
        PropTypes.arrayOf(PropTypes.node),
        PropTypes.node
    ])
};

export default Header;
