import React from 'react';
import classnames from 'classnames';

const Button = (props) => {
    return (
        <button
            type="button"
            onClick={props.onClick}
            className={classnames("button", props.className)}
            disabled={props.disabled}
        >
            {props.children}
        </button>
    );
}

export default Button;