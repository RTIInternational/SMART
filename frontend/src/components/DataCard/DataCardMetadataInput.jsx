import React from "react";
import { Form } from "react-bootstrap";

const DataCardMetadataInput = ({ label, value, updateMetadata }) => {
    return (
        <Form.Group>
            <Form.Label style={{ marginRight: "4px" }}>{label}: </Form.Label>
            <Form.Control
                as="input"
                onChange={(e) => updateMetadata(label, e.target.value)}
                type="text"
                value={value}
            />
        </Form.Group>
    );
};

export default DataCardMetadataInput;
