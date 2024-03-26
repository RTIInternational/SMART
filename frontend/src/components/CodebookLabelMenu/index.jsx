import React from 'react';
import { Button, ButtonGroup, Modal } from "react-bootstrap";

const CODEBOOK_URL = window.CODEBOOK_URL;


class CodebookLabelMenu extends React.Component {

    constructor(props){
        super(props);
        this.toggleCodebook = this.toggleCodebook.bind(this);
        this.state = {
            codebook_open: false
        };
    }

    //This opens/closes the codebook module
    toggleCodebook(){
        this.setState({ codebook_open: !this.state.codebook_open });
    }

    render() {
        let codebook_module, codebook_button;

        if (CODEBOOK_URL != "") {
            codebook_module = (
                <Modal dialogClassName="codebook-modal" style={{ opacity: 1 }} show={this.state.codebook_open} onHide={this.toggleCodebook}>
                    <Modal.Header closeButton>
                        <Modal.Title>Codebook</Modal.Title>
                    </Modal.Header>
                    <Modal.Body>
                        <embed
                            type="application/pdf"
                            src={CODEBOOK_URL}
                            id="pdf_document"
                            width="100%"
                            height="100%" />
                    </Modal.Body>
                </Modal>
            );
            codebook_button = (
                <Button onClick={this.toggleCodebook} className="codebook-btn">Codebook</Button>
            );
        } else {
            codebook_module = (<div />);
            codebook_button = (<div />);
        }

        return (
            <div className="margin-bottom-15 no-overflow">
                <div className="row" id="label_group_buttons">
                    {CODEBOOK_URL != "" ? (
                        <ButtonGroup className="pull-left">
                            {codebook_button}
                        </ButtonGroup>
                    ) : null}
                </div>
                {codebook_module}
            </div>
        );
    }
}

CodebookLabelMenu.propTypes = {};

export default CodebookLabelMenu;
