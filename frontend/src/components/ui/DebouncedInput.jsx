import React, { useEffect } from "react";
import { Form } from "react-bootstrap";

const DebouncedInput = ({ onChange, placeholder, value: initialValue }) => {
    const [value, setValue] = React.useState(initialValue);
  
    useEffect(() => {
        setValue(initialValue);
    }, [initialValue]);
  
    useEffect(() => {
        const timeout = setTimeout(() => {
            onChange(value);
        }, 500);
  
        return () => clearTimeout(timeout);
    }, [value]);
  
    return (
        <Form.Control
            as="input"
            className="w-auto"
            onChange={(event) => setValue(event.target.value)}
            placeholder={placeholder}
            type="text"
            value={value || ""}
        />
    );
};

export default DebouncedInput;
