import React from "react";
import PropTypes from "prop-types";
import {
    Button,
    ButtonToolbar,
    Clearfix,
    Tooltip,
    OverlayTrigger,
    Alert
} from "react-bootstrap";

class LabelForm extends React.Component {
    constructor(props) {
        super(props);

        let selected_label = {
            name: null,
            pk: null
        };

        if (this.props.previousLabel != null) {
            selected_label = {
                name: this.props.previousLabel.name,
                pk: this.props.previousLabel.pk
            };
        }

        this.state = {
            label_reason: "",
            selected_label: selected_label,
            error_message: null
        };

        this.handleReasonChange = this.handleReasonChange.bind(this);
        this.handleLabelSelect = this.handleLabelSelect.bind(this);
        this.handleSubmitLabel = this.handleSubmitLabel.bind(this);

        this.warningRender = this.warningRender.bind(this);
        this.passRender = this.passRender.bind(this);
        this.discardRender = this.discardRender.bind(this);

        this.skipData = this.skipData.bind(this);
        this.annotateData = this.annotateData.bind(this);
    }

    handleReasonChange(event) {
        this.setState({
            label_reason: event.target.value
        });
    }

    handleLabelSelect(option) {
        /* This function is for when a label is selected*/
        this.setState({
            selected_label: { name: option.name, pk: option.pk }
        });
    }

    handleSubmitLabel(event) {
        /* This function is for when the form is submitted*/
        if (this.state.selected_label.name == null) {
            this.setState({
                error_message: "Error: You must choose a label!"
            });
            event.preventDefault();
        } else {
            this.annotateData();
            this.setState({
                label_reason: "",
                selected_label: { name: null, pk: null },
                error_message: null
            });
            event.preventDefault();
        }
    }

    warningRender() {
        /* This function is for rendering the error message*/
        if (this.state.error_message == null) {
            return <div></div>;
        } else {
            return <Alert bsStyle="danger">{this.state.error_message}</Alert>;
        }
    }

    skipData() {
        /* This function handles the logic for calling skip functions*/

        if (this.props.optionalInt != null) {
            this.props.skipFunction(this.props.data, this.props.optionalInt);
        } else if (this.props.previousLabel != null) {
            this.props.skipFunction(this.props.data, this.props.previousLabel.pk);
        } else {
            this.props.skipFunction(this.props.data);
        }
    }

    annotateData() {
        /* This function handles the logic for calling annotate functions*/
        if (this.props.optionalInt != null) {
            this.props.labelFunction(
                this.props.data,
                this.state.selected_label.pk,
                this.state.label_reason,
                this.props.optionalInt
            );
        } else if (this.props.previousLabel != null) {
            this.props.labelFunction(
                this.props.data,
                this.props.previousLabel.pk,
                this.state.selected_label.pk,
                this.state.label_reason
            );
        } else {
            this.props.labelFunction(
                this.props.data,
                this.state.selected_label.pk,
                this.state.label_reason
            );
        }
    }

    passRender() {
        /* This function handles the logic for rendering the skip button*/
        if (this.props.passButton) {
            return (
                <OverlayTrigger
                    placement="top"
                    overlay={
                        <Tooltip id="skip_tooltip">
                            Clicking this button will send this document to an
                            administrator for review
                        </Tooltip>
                    }
                >
                    <Button
                        onClick={() => {
                            this.skipData();
                        }}
                        bsStyle="danger"
                    >
                        Skip
                    </Button>
                </OverlayTrigger>
            );
        } else {
            return <div></div>;
        }
    }

    discardRender() {
        /* This function handles the logic for rendering the discard button*/
        if (this.props.discardButton) {
            return (
                <OverlayTrigger
                    placement="top"
                    overlay={
                        <Tooltip id="discard_tooltip">
                            This marks this data as uncodable, and will remove
                            it from the active data in this project.
                        </Tooltip>
                    }
                >
                    <Button
                        onClick={() => {
                            this.props.discardFunction(this.props.data);
                        }}
                        bsStyle="danger"
                    >
                        Discard
                    </Button>
                </OverlayTrigger>
            );
        } else {
            return <div></div>;
        }
    }

    render() {
        const { labels } = this.props;
        return (
            <form onSubmit={this.handleSubmitLabel}>
                <ButtonToolbar>
                    {labels.map(opt => (
                        <Button
                            key={`deck-button-${opt["name"]}`}
                            bsStyle="info"
                            onClick={() => this.handleLabelSelect(opt)}
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
                    {this.passRender()}
                    {this.discardRender()}
                    <Button type="submit" bsStyle="success">
                        Submit
                    </Button>
                </ButtonToolbar>
                <Clearfix />
            </form>
        );
    }
}

LabelForm.propTypes = {
    data: PropTypes.object,
    previousLabel: PropTypes.object,
    labelFunction: PropTypes.func.isRequired,
    passButton: PropTypes.boolean,
    discardButton: PropTypes.boolean,
    skipFunction: PropTypes.func.isRequired,
    discardFunction: PropTypes.func.isRequired,
    labels: PropTypes.arrayOf(PropTypes.object),
    optionalInt: PropTypes.integer
};

export default LabelForm;
