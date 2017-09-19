import React from 'react';
import PropTypes from 'prop-types';
import classnames from 'classnames';

const Card = (props) => (
    <div className={classnames("card", "clearfix", props.className)} style={props.style}>
        <div className="cardface">
            {props.children}
        </div>
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
