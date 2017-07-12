import React from 'react';
import { Form, FormGroup, ControlLabel, FormControl, Button } from "react-bootstrap";

class Login extends React.Component {
    handleLogin(e) {
        e.preventDefault();

        if (!this._inputUser.value || !this._inputPW.value) {
            return;
        }

        const loginData = {
            username: this._inputUser.value,
            password: this._inputPW.value
        };

        this.props.login(loginData);
    }

    render() {
        return (
            <Form>
                 <FormGroup controlId="login-username">
                    <ControlLabel>
                        User Name
                    </ControlLabel>
                    <FormControl 
                        type="text"
                        placeholder="User Name"
                        inputRef={ref => { this._inputUser = ref; }}
                    />
                </FormGroup>
                <FormGroup controlId="login-password">
                    <ControlLabel>
                        Password
                    </ControlLabel>
                    <FormControl
                        type="password"
                        placeholder="Password"
                        inputRef={ref => { this._inputPW = ref; }}
                    />
                </FormGroup> 
                <FormGroup>
                    <Button bsStyle="primary" type="submit" onClick={(e) => this.handleLogin(e)}>
                        Sign in
                    </Button>
                </FormGroup>
            </Form>
        );
    };
}

export default Login;
