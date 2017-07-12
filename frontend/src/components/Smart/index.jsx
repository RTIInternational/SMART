import React from 'react';
import { Button } from "react-bootstrap";

import Deck from '../Deck';
import Header from '../Header';
import Login from '../Login';

class Smart extends React.Component {
    render() {
        let children = null;
        let headerAside = null;

        if (this.props.token) {
            children = (
                <Deck 
                    fetchCards={this.props.fetchCards}
                    passCard={this.props.passCard}
                    popCard={this.props.popCard}
                    cards={this.props.cards}
                />
            );

            headerAside = (
                <Button 
                    bsStyle="primary"
                    type="submit"
                    onClick={() => this.props.logout()}
                >
                    Logout
                </Button>
            );
        }
        else {
            children = <Login login={this.props.login} />
        }

        return (
           <div>
                <Header>
                    {headerAside}
                </Header>
                <main>
                    {children}
                </main>
            </div>
        );
    }
};

export default Smart;
