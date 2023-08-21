import React, { Fragment, useState, useEffect } from "react";
import { Button } from "react-bootstrap";

import DataCardMetadataInput from "./DataCardMetadataInput";
import { useMetadataValue } from "../../hooks";
import { GrayBox, H4 } from "../ui";

const DataCardMetadata = ({ cardData }) => {
    const { dataID, metadata: initialMetadata } = cardData;
    const { mutate } = useMetadataValue();
    const parseMetadata = (md) => md.reduce((a, b) => {
        const [key, value] = b.split(': ');
        a[key] = value;
        return a;
    }, {});
    const [edit, setEdit] = useState(false);

    const [originalMetadata, setOriginalMetadata] = useState(parseMetadata(initialMetadata));
    const [metadata, setMetadata] = useState(originalMetadata || []);

    useEffect(() => {
        setOriginalMetadata(parseMetadata(initialMetadata));
        setMetadata(parseMetadata(initialMetadata) || []);
    }, [initialMetadata]);

    const handleSubmit = (event) => {
        event.preventDefault();
        setEdit(false);
        mutate({
            dataID, 
            metadatas: Object.entries(metadata).filter(([key, value]) =>
                originalMetadata[key] !== value
            ).map(([key, value]) => ({ key, previous: originalMetadata[key], value }))
        });

        setOriginalMetadata(metadata);
    };

    const reset = () => {
        setEdit(false);
        setMetadata(originalMetadata);
    };

    const updateMetadata = (key, value) => {
        setMetadata(previousMetadata => Object.assign({}, previousMetadata, { [key]: value }));
    };

    if (metadata.length == 0)
        return <p></p>;
    
    const Element = edit ? "form" : "div";

    if (Object.entries(metadata).length === 0) return null;
    
    return (
        <GrayBox>
            <Element onSubmit={handleSubmit}>
                <div className="align-items-end d-flex">
                    <div className="flex-fill">
                        <H4>Respondent Data</H4>
                    </div>
                    {(initialMetadata) && !edit && (
                        <Button
                            className="ml-3"
                            onClick={() => setEdit(true)}
                            type="button"
                            variant="info"
                        >
                            Edit
                        </Button>
                    )}
                    {(initialMetadata) && edit && (
                        <Fragment>
                            <Button
                                className="ml-3"
                                type="submit"
                                variant="info"
                            >
                                Save
                            </Button>
                            <Button
                                className="ml-2"
                                onClick={() => reset()}
                                type="button"
                                variant="info"
                            >
                                Cancel
                            </Button>
                        </Fragment>
                    )}
                </div>
                {Object.entries(metadata).map(([key, value]) => (
                    <Fragment key={key}>
                        {edit ? <DataCardMetadataInput label={key} value={value} updateMetadata={updateMetadata} /> : <p>{key}: {value}</p>}
                    </Fragment>
                ))}
            </Element>
        </GrayBox>
    );
};

export default DataCardMetadata;
