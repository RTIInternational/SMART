import React, { Fragment } from "react";
import { Card } from "react-bootstrap";

import DataCardAdjudicateButton from "./DataCardAdjudicateButton";
import DataCardMetadata from "./DataCardMetadata";
import DataCardSelectLabel from "./DataCardSelectLabel";
import DataCardSuggestedLabels from "./DataCardSuggestedLabels";
import DataCardText from "./DataCardText";
import { useModifyLabel, useChangeToSkip, useLabels } from "../../hooks";
import DataCardLabelButtons from "./DataCardLabelButtons";

const DataCard = ({ card, type }) => {
    const { data: labels } = useLabels();

    const { mutate: changeToSkip } = useChangeToSkip();
    const { mutate: modfiyLabel } = useModifyLabel();

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
            {labels && (
                <Fragment>
                    {labels.labels.length <= 5 ? (
                        <DataCardLabelButtons
                            card={card}
                            fn={type === "history" ? modfiyLabel : () => { }}
                        />
                    ) : (
                        <Fragment>
                            <DataCardSuggestedLabels
                                card={card}
                                fn={type === "history" ? modfiyLabel : () => { }}
                            />
                            <DataCardSelectLabel
                                card={card}
                                fn={type === "history" ? modfiyLabel : () => { }}
                            />
                        </Fragment>
                    )}
                </Fragment>
            )}
        </Card>
    );
};

export default DataCard;
