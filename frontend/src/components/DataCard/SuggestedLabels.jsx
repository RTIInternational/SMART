import React from "react";

export default function SuggestedLabels({ card, labels }) {
    if (labels.length <= 5) {
        return null;
    }

    return (
        <div className="suggestions">
            <h4>Suggested Labels</h4>
            {card.text.similarityPair.slice(0, 5).map((opt, index) => (
                <div key={index + 1} className="">{index + 1}. {opt.split(':')[0]}</div>
            ))}
        </div>
    );
}
