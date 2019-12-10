import React from "react";
import PropTypes from "prop-types";
import {
    Button,
    ButtonToolbar,
    Clearfix,
    Well,
    Tooltip,
    OverlayTrigger,
    Alert
} from "react-bootstrap";

const ADMIN = window.ADMIN;

class Card extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            label_reason: "",
            selected_label: { name: null, pk: null },
            error_message: null
        };

        this.handleReasonChange = this.handleReasonChange.bind(this);
        this.handleLabelSelect = this.handleLabelSelect.bind(this);
        this.handleSubmitLabel = this.handleSubmitLabel.bind(this);
        this.warningRender = this.warningRender.bind(this);
    }

    handleReasonChange(event) {
        this.setState({
            label_reason: event.target.value
        });
    }

    handleLabelSelect(option) {
        this.setState({
            selected_label: { name: option.name, pk: option.pk }
        });
    }

    handleSubmitLabel(event) {
        if (this.state.selected_label.name == null) {
            this.setState({
                error_message: "Error: You must choose a label!"
            });
            event.preventDefault();
        } else {
            this.props.annotateCard(
                this.props.cards[0],
                this.state.selected_label.pk,
                this.state.label_reason,
                this.props.cards.length,
                ADMIN
            );
            this.setState({
                label_reason: "",
                selected_label: { name: null, pk: null },
                error_message: null
            });
            event.preventDefault();
        }
    }

    warningRender() {
        if (this.state.error_message == null) {
            return <div></div>;
        } else {
            return <Alert bsStyle="danger">{this.state.error_message}</Alert>;
        }
    }

    componentWillMount() {
        this.props.fetchCards();
    }

    render() {
        let card;
        const { message, cards, passCard, labels } = this.props;

        if (!(cards === undefined) && cards.length > 0) {
            //just get the labels from the cards
            card = (
                <div className="full" key={cards[0].id}>
                    <div className="cardface">
                        <h2> Card {cards[0].id + 1} </h2>
                        <p> {cards[0].text["text"]} </p>
                        <form onSubmit={this.handleSubmitLabel}>
                            <ButtonToolbar>
                                {labels.map(opt => (
                                    <Button
                                        key={`deck-button-${opt["name"]}`}
                                        bsStyle="info"
                                        onClick={() =>
                                            this.handleLabelSelect(opt)
                                        }
                                    >
                                        {opt["name"]}
                                    </Button>
                                ))}
                                <p>
                                    (Optional) Reason for Label:
                                    <input
                                        type="text"
                                        value={this.state.label_reason}
                                        onChange={this.handleReasonChange}
                                    />
                                </p>
                                <b>Label: {this.state.selected_label.name}</b>
                            </ButtonToolbar>

                            <ButtonToolbar bsClass="btn-toolbar pull-right">
                                {this.warningRender()}
                                <Button type="submit" bsStyle="success">
                                    Submit
                                </Button>
                                <OverlayTrigger
                                    placement="top"
                                    overlay={
                                        <Tooltip id="skip_tooltip">
                                            Clicking this button will send this
                                            document to an administrator for
                                            review
                                        </Tooltip>
                                    }
                                >
                                    <Button
                                        onClick={() => {
                                            passCard(
                                                cards[0],
                                                cards.length,
                                                ADMIN
                                            );
                                        }}
                                        bsStyle="danger"
                                    >
                                        Skip
                                    </Button>
                                </OverlayTrigger>
                            </ButtonToolbar>
                            <Clearfix />
                        </form>
                    </div>
                </div>
            );
        } else {
            let blankDeckMessage = message
                ? message
                : "No more data to label at this time. Please check back later";
            card = <Well bsSize="large"> {blankDeckMessage} </Well>;
        }

        return card;
    }
}

Card.propTypes = {
    cards: PropTypes.arrayOf(PropTypes.object),
    message: PropTypes.string,
    fetchCards: PropTypes.func.isRequired,
    annotateCard: PropTypes.func.isRequired,
    passCard: PropTypes.func.isRequired,
    labels: PropTypes.arrayOf(PropTypes.object)
};

export default Card;
