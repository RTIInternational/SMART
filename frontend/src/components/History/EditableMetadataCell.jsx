import React, { useState } from "react";
import { DebounceInput } from "react-debounce-input";

export default function HistoryMetadataCell({ id, value, modifyMetadataValue }) {
    const [cellValue, setCellValue] = useState(value);

    const onCellValueChange = (event) => {
        setCellValue(event.target.value);
        modifyMetadataValue(id, event.target.value);
    };
    
    return (
        <div className="editable-cell">
            <DebounceInput debounceTimeout={300} value={cellValue} onChange={onCellValueChange} />
        </div>
    );
}
