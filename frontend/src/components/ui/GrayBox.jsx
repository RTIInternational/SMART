import React from "react";

const GrayBox = ({ children }) => {
    return (
        <div className="bg-gray px-3 py-2 rounded">
            {children}
        </div>
    );
};

export default GrayBox;
