import React from "react";

export default function CardData({ card }) {
    return (
        <div className="cardface-info">
            <h2>Card {card.id + 1}</h2>
            <div className="card-data">
                <h4>Text to Label</h4>
                <p>{card.text["text"] || card.text["data"]}</p>
            </div>
            {extractMetadata(card)}
        </div>
    );
}

function extractMetadata(card) {
    if (card.text["metadata"].length == 0) {
        return <p></p>;
    } else {
        return (
            <div className="card-metadata">
                <h4>Background Data</h4>
                {card.text["metadata"].map(val => (
                    <p key={val}>{val}</p>
                ))}
            </div>
        );
    }
}
