import React, { Fragment, useState } from "react";
import { Button, Form, Modal, OverlayTrigger, Tooltip } from "react-bootstrap";

const DataCardAdjudicateButton = ({ cardData, fn, }) => {

    const [isOpen, setIsOpen] = useState(false);
    const [message, setMessage] = useState("");

    const handleSkip = (event) => {
        event.preventDefault();
        // temporary stand-in for spread operator, should be fn({ ...cardData, message });
        const newCardData = Object.assign({}, cardData, { message });
        fn(newCardData);
        setIsOpen(false);
    };

    return (
        <Fragment>
            <OverlayTrigger
                overlay={
                    <Tooltip id="skip_tooltip">
                        Clicking this button will send this card to an administrator for review
                    </Tooltip>
                }
                placement="top"
            >
                <Button
                    onClick={() => setIsOpen(true)}
                    variant="info"
                >
                    Adjudicate
                </Button>
            </OverlayTrigger>
            
            {isOpen && (
                <Modal style={{ opacity: 1 }} show={isOpen} onHide={() => setIsOpen(false)}>
                    <Modal.Header closeButton>
                        <Modal.Title>Adjudicate</Modal.Title>
                    </Modal.Header>
                    <Modal.Body>
                        <p>Please enter the reasons for skipping this card:</p>
                        <Form onSubmit={handleSkip}>
                            <Form.Group>
                                <Form.Label>Reason</Form.Label>
                                <Form.Control
                                    as="textarea"
                                    onChange={(event) => setMessage(event.target.value)}
                                    placeholder="Reasons for skipping..."
                                    required
                                    rows={3}
                                />
                            </Form.Group>
                            <Button variant="primary" type="submit">Adjudicate</Button>
                        </Form>
                    </Modal.Body>
                </Modal>
            )}
        </Fragment>
    );
};

export default DataCardAdjudicateButton;
