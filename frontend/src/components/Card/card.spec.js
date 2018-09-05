import React, { Component } from 'react';
import { shallow } from 'enzyme';
import { assert } from 'chai';
import Card from './index';

describe('<Card />', () => {
    describe('render', () => {
        it('renders properly if all props provided', () => {
            const fn = () => {};
            const data = [];
            const message = "";
            const wrapper = shallow(
              <Card
                cards = {data}
                message = {message}
                fetchCards = {fn}
                annotateCard = {fn}
                passCard = {fn}
              />
            );
        });
    });
});
