import React, { Fragment } from "react";
import { Card, Table } from "react-bootstrap";

const IRRtable = ({ irrEntry }) => {
    if (!irrEntry || !Object.keys(irrEntry).length){
        return <Fragment>Error loading IRR data</Fragment>;
    }
    const { data_id, ...irrData } = irrEntry;
    return (
        <Card className="irr-card d-flex flex-column m-0 p-3" >
            <Table striped bordered hover>
                <thead>
                    <tr>
                        <th>User</th>
                        <th>Label</th>
                    </tr>
                </thead>
                <tbody>
                    {Object.entries(irrData).map(([user, label], index) => (
                        <tr key={index}>
                            <td style={{ wordWrap: "break-word", whiteSpace: "normal" }}>{user}</td>
                            <td style={{ wordWrap: "break-word", whiteSpace: "normal" }}>{label}</td>
                        </tr>
                    ))}
                </tbody>
            </Table>
        </Card>
    );
};

export default IRRtable;
