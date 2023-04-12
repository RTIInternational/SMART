import React, { Fragment, useState } from "react";

export default function Metadata({ card, modifyMetadataValues }) {
    const dataPk = card.text["pk"] || card.text["id"];

    const [edit, setEdit] = useState(false);
    const [originalMetadata, setOriginalMetadata] = useState(card.text["metadata"].reduce((a, b) => {
        const [key, value] = b.split(': ');
        a[key] = value;
        return a;
    }, {}));
    const [metadata, setMetadata] = useState(originalMetadata || []);

    function handleSubmit(e) {
        e.preventDefault();
        setEdit(false);
        
        modifyMetadataValues(dataPk, Object.entries(metadata).filter(([key, value]) =>
            originalMetadata[key] !== value
        ).map(([key, value]) => ({ key, previous: originalMetadata[key], value })));

        setOriginalMetadata(metadata);
    }

    function reset() {
        setEdit(false);
        setMetadata(originalMetadata);
    }

    function updateMetadata(key, value) {
        setMetadata(previousMetadata => Object.assign({}, previousMetadata, { [key]: value }));
    }

    if (metadata.length == 0)
        return <p></p>;
    
    const Element = edit ? "form" : "div";
    
    return (
        <Element className="card-metadata" onSubmit={handleSubmit}>
            <div className="card-metadata-header">
                <h4>Respondent Data</h4>
                {modifyMetadataValues && !edit && <button className="btn btn-info" onClick={() => setEdit(true)} type="button">
                    Edit
                </button>}
                {modifyMetadataValues && edit && (
                    <Fragment>
                        <button className="btn btn-info" type="submit">Save</button>
                        <button className="btn btn-info" onClick={() => reset()} type="button">
                            Cancel
                        </button>
                    </Fragment>
                )}
            </div>
            {Object.entries(metadata).map(([key, value]) => (
                <Fragment key={key}>{edit ? <MetadataInput label={key} value={value} updateMetadata={updateMetadata} /> : <p>{key}: {value}</p>}</Fragment>
            ))}
        </Element>
    );
}

function MetadataInput({ label, value, updateMetadata }) {
    return (
        <div className="form-group">
            <label className="control-label" style={{ marginRight: "4px" }}>{label}: </label>
            <input className="form-control" onChange={(e) => updateMetadata(label, e.target.value)} type="text" name="Text" value={value} />
        </div>
    );
}
