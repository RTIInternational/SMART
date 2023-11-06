import React from "react";

import { H4 } from "../ui";

const DataCardText = ({ cardData }) => {
    return (
        <div>
            <H4>Text to Label</H4>
            <p style={{ whiteSpace: "normal" }}>{cardData.text}</p>
        </div>
    );
};

export default DataCardText;
