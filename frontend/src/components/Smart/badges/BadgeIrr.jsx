import React, { Fragment } from "react";
import { Badge } from "react-bootstrap";

import { useAdminCounts } from "../../../hooks";

const BadgeIrr = () => {
    const { data: adminCounts } = useAdminCounts();

    if (!adminCounts || !adminCounts.data.IRR) return null;

    return (
        <Fragment>
            IRR
            <Badge className="tab-badge">
                {adminCounts.data.IRR}
            </Badge>
            | 
            <span> </span>
        </Fragment>
    );
};

export default BadgeIrr;
