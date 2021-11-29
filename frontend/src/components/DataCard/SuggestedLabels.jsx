import React from "react";
import * as stringSimilarity from "string-similarity";

export default function SuggestedLabels({ card, labels, onSelectLabel }) {
    if (labels.length <= 5) {
        return null;
    }

    // stringSimilarity.findBestMatch takes a string and an array of strings to preform the similarity comparisons
    // sort matches from best rating to lowest rating and splice to get first 5
    const labelStrings = labels.map(label => `${label.name} (${label.description})`);

    let matches = stringSimilarity.findBestMatch(card.text.text, labelStrings);
    matches = matches.ratings.sort((rating1, rating2) => parseFloat(rating2.rating) - parseFloat(rating1.rating)).slice(0, 5);    

    return (
        <div className="suggestions">
            <h4>Suggested Labels</h4>
            {matches.map((match, index) => (
                <button key={index + 1} onClick={() => onSelectLabel(card, labels.find(label => label.name === match.target.split(" ")[0]).pk)}>{index + 1}. {match.target}</button>
            ))}
        </div>
    );
}
