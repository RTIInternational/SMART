import React from 'react';
import PropTypes from 'prop-types';
import classnames from 'classnames';

const Card = (props) => (
    <div className={classnames("card", props.className)} style={props.style}>
        {props.children}
    </div>
);

Card.propTypes = {
    className: PropTypes.string,
    style: PropTypes.object,
    children: PropTypes.oneOfType([
        PropTypes.arrayOf(PropTypes.node),
        PropTypes.node
    ])
};

export default Card;
