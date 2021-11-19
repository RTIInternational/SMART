import React from "react";
import * as stringSimilarity from "string-similarity";

export default function SuggestedLabels({ card, labels }) {
    if (labels.length <= 5) {
        return null;
    }

    const labelStrings = labels.map(label => `${label.name} (${label.description})`);

    let matches = stringSimilarity.findBestMatch(card.text.text, labelStrings);
    matches = matches.ratings.sort((rating1, rating2) => parseFloat(rating2.rating) - parseFloat(rating1.rating)).slice(0, 5);

    return (
        <div className="suggestions">
            <h4>Suggested Labels</h4>
            {matches.map((match, index) => (
                <div key={index + 1} className="">{index + 1}. {match.target}</div>
            ))}
        </div>
    );
}
