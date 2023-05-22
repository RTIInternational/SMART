import React from "react";

import { H4 } from "../ui";

const DataCardText = ({ card }) => {
    return (
        <div>
            <H4>Text to Label</H4>
            <p>{card.data}</p>
        </div>
    );
};

export default DataCardText;
