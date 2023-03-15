import React, { useEffect, useState } from "react";
import { Spinner } from "react-bootstrap";

function handleErrors(res) {
    if (!res.ok) {
        throw Error(res.statusText);
    }
    return res;
}

export default function SuggestedLabels({ card, labels, onSelectLabel }) {
    const [suggestions, setSuggestions] = useState();
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let isMounted = true;
        fetch(`/api/comparisons/${card.text.project}?text=${card.text.text || card.text.data}`)
            .then(handleErrors)
            .then(res => res.json().then(result => {
                setLoading(false);
                if (isMounted) setSuggestions(result);
            }))
            .catch(error => console.log(error));
        return () => {
            isMounted = false;
            setSuggestions();
        };
    }, []);

    if (!labels) {
        return null;
    }
    return (
        (loading || !suggestions) ?
            <div className="suggestions">
                <div>
                    <Spinner animation="border" role="status"/>
                </div>
                <span className="visually-hidden">Loading labels...</span>
            </div> :
            <div className="suggestions">
                <h4>Suggested Labels</h4>
                {suggestions.suggestions.map((suggestion, index) => (
                    <button key={index + 1} onClick={() => onSelectLabel(card, suggestion.pk)}>
                        {`${suggestion.name}: ${suggestion.description}`}
                    </button>
                ))}
            </div>
            
    );
}
