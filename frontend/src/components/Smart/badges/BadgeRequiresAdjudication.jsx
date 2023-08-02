import React from "react";
import { Badge } from "react-bootstrap";

import { useAdminCounts } from "../../../hooks";

const BadgeRequiresAdjudication = () => {
    const { data: adminCounts } = useAdminCounts();

    if (!adminCounts) return null;

    return (
        <Badge className="tab-badge">
            {adminCounts.data.SKIP}
        </Badge>
    );
};

export default BadgeRequiresAdjudication;

