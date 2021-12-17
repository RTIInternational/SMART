import React, { useEffect, useState } from "react";
import { fetchSuggestions } from '../../actions/card';

export default function SuggestedLabels({ card, labels, onSelectLabel }) {
    const [suggestions, setSuggestions] = useState();

    useEffect(() => {
        fetch(`/api/embeddings/${card.text.project}?text=${card.text.text}`)
            .then(res => res.json().then(result => setSuggestions(result)));
    }, []);

    if (labels.length <= 5 || !suggestions) {
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
