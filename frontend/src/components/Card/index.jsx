import React from 'react';
import classnames from 'classnames';

const Card = (props) => (
    <div className={classnames("card", props.className)} style={props.style}>
        {props.children}
    </div>
);

export default Card;