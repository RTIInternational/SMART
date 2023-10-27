import React from "react";
import { Button, Modal } from "react-bootstrap";

const ConfirmationModal = ({ fn, showModal, setSelectedLabelID }) => {
    return (
        <Modal
            centered
            show={showModal}
            onHide={() => setSelectedLabelID(null)}
            animation={false}>
            <Modal.Header closeButton>
                <Modal.Title>Confirmation</Modal.Title>
            </Modal.Header>
            <Modal.Body>Are you sure you want to change labels?</Modal.Body>
            <Modal.Footer>
                <Button variant="secondary" onClick={ () => {
                    setSelectedLabelID(null);
                }}>
                        Cancel
                </Button>
                <Button variant="primary" onClick={ () => {
                    fn();
                    setSelectedLabelID(null);
                }}>
                        Confirm change
                </Button>
            </Modal.Footer>
        </Modal>
    );

};

export default ConfirmationModal;
