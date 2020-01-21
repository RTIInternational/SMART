import React from 'react';
import PropTypes from 'prop-types';
import {
    Button,
    ButtonToolbar,
    Clearfix,
    Checkbox,
    Tooltip,
    OverlayTrigger,
    Alert,
    Radio,
    DropdownButton,
    MenuItem,
    FormGroup,
    FormControl
} from 'react-bootstrap';

class LabelForm extends React.Component {
    constructor(props) {
        super(props);

        let selected_label = {
            name: "Choose a label",
            pk: null
        };
        let labelReason = "";
        let is_explicit = false;

        if (this.props.previousLabel != null) {
            selected_label = {
                name: this.props.previousLabel.name,
                pk: this.props.previousLabel.pk
            };
            labelReason = this.props.previousLabel.reason;
            is_explicit = this.props.previousLabel.is_explicit;
        }


        this.state = {
            label_reason: labelReason,
            selected_label: selected_label,
            error_message: null,
            is_explicit: is_explicit
        };

        this.handleReasonChange = this.handleReasonChange.bind(this);
        this.handleLabelSelect = this.handleLabelSelect.bind(this);
        this.handleSubmitLabel = this.handleSubmitLabel.bind(this);
        this.handleChangeExplict = this.handleChangeExplict.bind(this);

        this.warningRender = this.warningRender.bind(this);
        this.passRender = this.passRender.bind(this);
        this.discardRender = this.discardRender.bind(this);
        this.labelButtonRender = this.labelButtonRender.bind(this);
        this.explicitRender = this.explicitRender.bind(this);

        this.skipData = this.skipData.bind(this);
        this.annotateData = this.annotateData.bind(this);
    }

    handleChangeExplict(){
        this.setState({ is_explicit: !this.state.is_explicit });
    }

    explicitRender() {
        if (this.props.hasExplicit) {
            return (
                <OverlayTrigger
                    placement="top"
                    overlay={
                        <Tooltip id="explicit_tooltip">
                            This marks this data as explicit, and must be sent
                            to an administrator for review.
                        </Tooltip>
                    }
                >
                    <Checkbox onClick={this.handleChangeExplict} defaultChecked={this.state.is_explicit}> <b>Explicit</b> </Checkbox>
                </OverlayTrigger>
            );
        } else {
            return null;
        }
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
        if (this.state.selected_label.pk == null) {
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
            this.props.skipFunction(this.props.data, this.props.optionalInt, this.state.is_explicit);
        } else if (this.props.previousLabel != null) {
            this.props.skipFunction(this.props.data, this.props.previousLabel.pk, this.state.is_explicit);
        } else {
            this.props.skipFunction(this.props.data, this.state.is_explicit);
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
        } else if (this.props.hasExplicit && !this.props.passButton){
            this.props.labelFunction(
                this.props.data,
                this.state.selected_label.pk,
                this.state.label_reason,
                this.state.is_explicit
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
            return null;
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
            return null;
        }
    }

    labelButtonRender(labels) {
        if (labels.length < 5) {
            return (
                <ButtonToolbar>
                    {labels.map(opt => (
                        <Radio
                            name="labelGroup"
                            key={`deck-button-${opt["name"]}`}
                            onClick={() => this.handleLabelSelect(opt)}
                            defaultChecked={(this.state.selected_label.pk === null ||
                              (this.state.selected_label.pk !== null &&
                                this.state.selected_label.name !== opt["name"] )) ? false : true}
                        >
                            {opt["name"]}
                        </Radio>
                    ))}
                </ButtonToolbar>
            );
        } else {
            return (
                <div>
                    <DropdownButton
                        id="label-dropdown"
                        title={(this.state.selected_label.pk === null) ? "Choose a Label" : this.state.selected_label.name}
                        bsStyle="info"
                    >
                        {labels.map(opt => (
                            <MenuItem
                                key={`deck-button-${opt["name"]}`}
                                onSelect={() => this.handleLabelSelect(opt)}
                            >
                                {opt["name"]}
                            </MenuItem>
                        ))}
                    </DropdownButton>
                </div>
            );
        }
    }

    render() {
        const { labels } = this.props;
        return (
            <form onSubmit={this.handleSubmitLabel}>
                <FormGroup>
                    {this.labelButtonRender(labels)}
                    <p>
                        (Optional) Reason for Label:
                        <FormControl
                            componentClass="textarea"
                            placeholder={(this.state.label_reason === "") ? "Type reason here" : this.state.label_reason}
                            onChange={this.handleReasonChange}
                        />
                    </p>
                    {this.warningRender()}
                    <ButtonToolbar bsClass="btn-toolbar pull-right">
                        {this.explicitRender()}
                        {this.passRender()}
                        {this.discardRender()}
                        <Button type="submit" bsStyle="success" disabled={this.state.is_explicit && this.props.passButton}>
                            Submit
                        </Button>
                    </ButtonToolbar>
                    <Clearfix />
                </FormGroup>
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
    optionalInt: PropTypes.integer,
    hasExplicit: PropTypes.boolean
};

export default LabelForm;
