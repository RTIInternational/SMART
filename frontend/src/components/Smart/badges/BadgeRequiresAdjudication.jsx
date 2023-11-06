import React, { Fragment } from "react";
import { Badge } from "react-bootstrap";

import { useAdminCounts } from "../../../hooks";

const BadgeRequiresAdjudication = () => {
    const { data: adminCounts } = useAdminCounts();

    if (!adminCounts) return null;

    return (
        <Fragment>
            Requires Adjudication
            <Badge className="tab-badge">
                {adminCounts.data.SKIP}
            </Badge>
        </Fragment>
    );
};

export default BadgeRequiresAdjudication;

