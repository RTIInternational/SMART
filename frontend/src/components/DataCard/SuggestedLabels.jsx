import React, { useEffect, useState } from "react";

function handleErrors(res) {
    if (!res.ok) {
        throw Error(res.statusText);
    }
    return res;
}

export default function SuggestedLabels({ card, labels, onSelectLabel }) {
    const [suggestions, setSuggestions] = useState();

    useEffect(() => {
        fetch(`/api/comparisons/${card.text.project}?text=${card.text.text || card.text.data}`)
            .then(handleErrors)
            .then(res => res.json().then(result => setSuggestions(result)))
            .catch(error => console.log(error) );
    }, []);

    if (!labels || labels.length <= 5 || !suggestions) {
        return null;
    }

    return (
        <div className="suggestions">
            <h4>Suggested Labels</h4>
            {suggestions.suggestions.map((suggestion, index) => (
                <button key={index + 1} onClick={() => onSelectLabel(card, suggestion.pk)}>
                    {index + 1}. {`${suggestion.name}: ${suggestion.description}`}
                </button>
            ))}
        </div>
    );
}
