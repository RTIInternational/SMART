import React from 'react';
import PropTypes from 'prop-types';
import { Button, ButtonGroup,
    Glyphicon, Modal  } from "react-bootstrap";
const CODEBOOK_URL = window.CODEBOOK_URL;
class CodebookLabelMenu extends React.Component {

    constructor(props){
        super(props);
        this.toggleCodebook = this.toggleCodebook.bind(this);
        this.toggleLabel = this.toggleLabel.bind(this);
        this.getLabels = this.getLabels.bind(this);
        this.state = {
            codebook_open: false,
            labels_open: false
        }
    }

    //This opens/closes the codebook module
    toggleCodebook(){
        this.setState({codebook_open: !this.state.codebook_open});
    }

    toggleLabel(){
        this.setState({labels_open: !this.state.labels_open});
    }


    getLabels(labels, labels_open) {
        if(labels_open) {
            return (
                <div className="row">
                    <div className="col-md-12">
                        <ul className="list-group-flush">
                            {labels.map( (label) => (
                                <li className="list-group-item" key={label.pk}>
                                    <dt>{label.name}</dt>
                                    <dd>{label.description}</dd>
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>
            )
        } else {
            return null;
        }
    }

    render() {
        const {labels} = this.props;

        if(CODEBOOK_URL != "") {
            var codebook_module = (
                <Modal show={this.state.codebook_open} onHide={this.toggleCodebook}>
                    <Modal.Header closeButton>
                        <Modal.Title>Codebook</Modal.Title>
                    </Modal.Header>
                    <Modal.Body>
                        <embed
                            type="application/pdf"
                            src={CODEBOOK_URL}
                            id="pdf_document"
                            width="100%"
                            height="100%"
                        />
                    </Modal.Body>
                </Modal>
            );
            var codebook_button = (
                <Button onClick={this.toggleCodebook} className="codebook-btn">Codebook</Button>
            );
        } else {
            codebook_module = (<div />);
            codebook_button = (<div />);
        }

        if(this.state.labels_open) {
            var label_button = (
                <Button
                    onClick={this.toggleLabel}
                    className="minus_button"
                    bsStyle="danger"
                >
                    <Glyphicon glyph="minus"/> Label Guide
                </Button>
            )
        } else {
            label_button = (
                <Button
                    onClick={this.toggleLabel}
                    className="plus_button"
                    bsStyle="success"
                >
                    <Glyphicon glyph="plus"/> Label Guide
                </Button>
            )
        }

        return (
            <div className="margin-bottom-15 no-overflow">
                <div className="row" id="label_group_buttons">
                    <ButtonGroup className="pull-left">
                        {label_button}
                        {codebook_button}
                    </ButtonGroup>
                </div>
                {this.getLabels(labels, this.state.labels_open)}
                {codebook_module}
            </div>
        );

    }

}


CodebookLabelMenu.propTypes = {
    labels: PropTypes.arrayOf(PropTypes.object)
};

export default CodebookLabelMenu;
