import React from "react";
import { Card } from "react-bootstrap";

import DataCardAdjudicateButton from "./DataCardAdjudicateButton";
import DataCardMetadata from "./DataCardMetadata";
import DataCardSelectLabel from "./DataCardSelectLabel";
import DataCardSuggestedLabels from "./DataCardSuggestedLabels";
import DataCardText from "./DataCardText";
import { useChangeLabel, useChangeToSkip } from "../../hooks";

const DataCard = ({ card, type }) => {
    const { mutate: changeLabel } = useChangeLabel();
    const { mutate: changeToSkip } = useChangeToSkip();

    return (
        <Card className="d-flex flex-column m-0 p-3" style={{ gap: "1rem", maxWidth: "992px" }}>
            <div className="align-items-end d-flex justify-content-end mb-n2">
                <DataCardAdjudicateButton
                    dataID={card.id}
                    fn={type === "history" ? changeToSkip : () => {}}
                    oldLabelID={card.labelID}
                />
            </div>
            <DataCardText card={card} />
            <DataCardMetadata card={card} />
            <DataCardSuggestedLabels
                card={card}
                fn={type === "history" ? changeLabel : () => { }}
            />
            <DataCardSelectLabel
                card={card}
                fn={type === "history" ? changeLabel : () => { }}
            />
        </Card>
    );
};

export default DataCard;
