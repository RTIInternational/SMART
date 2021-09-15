import React from "react";
import PropTypes from "prop-types";
import {
    Button,
    ButtonToolbar,
    Card,
    Tooltip,
    OverlayTrigger
} from "react-bootstrap";
import Select from "react-dropdown-select";

const ADMIN = window.ADMIN;

class DataCard extends React.Component {
    componentDidMount() {
        //Don't fetch cards unless you don't have any
        //NOTE: otherwise it appends the same cards
        //to the current list again.
        if (this.props.cards.length == 0) {
            this.props.fetchCards();
        }
    }

    getText(card) {
        if (card.text["metadata"].length == 0) {
            return <p></p>;
        } else {
            return (
                <div>
                    <u>Background Data</u>
                    {card.text["metadata"].map(val => (
                        <p key={val}>{val}</p>
                    ))}
                    <u>Text to Label</u>
                </div>
            );
        }
    }

    render() {
        let card;

        const { labels, message, cards, passCard, annotateCard } = this.props;

        let labelsOptions = labels.map(label =>
            Object.assign(label, { value: label["pk"], dropdownLabel: `${label["name"]} ${label["description"] !== '' ? '(' + label["description"] + ')' : ''}` })
        );

        if (!(cards === undefined) && cards.length > 0) {
            //just get the labels from the cards
            card = (
                <div className="full" key={cards[0].id}>
                    <div className="cardface cardface-datacard clearfix">
                        <div className="cardface-info">
                            <h2>Card {cards[0].id + 1}</h2>
                            {this.getText(cards[0])}
                            <p>{cards[0].text["text"]}</p>
                        </div>
                        {labels.length > 5 && (
                            <div className="suggestions">
                                <h4>Suggested Labels</h4>
                                {cards[0].text.similarityPair.slice(0, 5).map((opt, index) => (
                                    <div key={index + 1} className="">{index + 1}. {opt.split(':')[0]}</div>
                                ))}
                            </div>
                        )}
                        <ButtonToolbar className="btn-toolbar">
                            {labels.length > 5 ? (
                                <Select
                                    className="align-items-center flex py-1 px-2"
                                    dropdownHandle={false}
                                    labelField="dropdownLabel"
                                    onChange={value =>
                                        annotateCard(
                                            cards[0],
                                            value[0]["pk"],
                                            cards.length,
                                            ADMIN
                                        )
                                    }
                                    options={labelsOptions}
                                    placeholder="Select label..."
                                    searchBy="dropdownLabel"
                                    sortBy="dropdownLabel"
                                    style={{ minWidth: "200px" }}
                                />
                            ) : (
                                labels.map(opt => (
                                    <Button
                                        onClick={() =>
                                            annotateCard(
                                                cards[0],
                                                opt["pk"],
                                                cards.length,
                                                ADMIN
                                            )
                                        }
                                        variant="primary"
                                        key={`deck-button-${opt["name"]}`}
                                    >
                                        {opt["name"]}
                                    </Button>
                                ))
                            )}
                            <OverlayTrigger
                                placement="top"
                                overlay={
                                    <Tooltip id="skip_tooltip">
                                        Clicking this button will send this
                                        document to an administrator for review
                                    </Tooltip>
                                }
                            >
                                <Button
                                    onClick={() => {
                                        passCard(cards[0], cards.length, ADMIN);
                                    }}
                                    variant="info"
                                >
                                    Skip
                                </Button>
                            </OverlayTrigger>
                        </ButtonToolbar>
                    </div>
                </div>
            );
        } else {
            let blankDeckMessage = message
                ? message
                : "No more data to label at this time. Please check back later";
            card = <Card body>{blankDeckMessage}</Card>;
        }

        return card;
    }
}

DataCard.propTypes = {
    cards: PropTypes.arrayOf(PropTypes.object),
    message: PropTypes.string,
    fetchCards: PropTypes.func.isRequired,
    annotateCard: PropTypes.func.isRequired,
    passCard: PropTypes.func.isRequired,
    labels: PropTypes.arrayOf(PropTypes.object)
};

export default DataCard;
