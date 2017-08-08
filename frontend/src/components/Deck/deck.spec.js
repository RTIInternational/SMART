import React, { Component } from 'react';
import { shallow } from 'enzyme';
import { assert } from 'chai';
import Deck from './index';

describe('<Deck />', () => {
    describe('render', () => {
        it('renders properly if all props provided', () => {
            const cards = [];
            
            const fn = () => {};

            const wrapper = shallow(
                <Deck 
                    fetchCards={fn}
                    passCard={fn}
                    popCard={fn}
                    cards={cards}
                />
            );
        });
    });
});
