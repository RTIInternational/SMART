import React from "react";
import PropTypes from "prop-types";
import {
    Button,
    ButtonToolbar,
    Card,
    Tooltip,
    OverlayTrigger
} from "react-bootstrap";

const ADMIN = window.ADMIN;

class DataCard extends React.Component {
    componentDidMount() {
        this.props.fetchCards();
    }

    render() {
        let card;
        const { labels, message, cards, passCard, annotateCard } = this.props;

        if (!(cards === undefined) && cards.length > 0) {
            //just get the labels from the cards
            card = (
                <div className="full" key={cards[0].id}>
                    <div className="cardface clearfix">
                        <h2>Card {cards[0].id + 1}</h2>
                        <p>{cards[0].text["text"]}</p>
                        <ButtonToolbar className="btn-toolbar pull-right">
                            {labels.map(opt => (
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
                            ))}
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
