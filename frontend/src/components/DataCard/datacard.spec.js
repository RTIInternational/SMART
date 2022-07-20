import React, { Component } from 'react';
import { shallow } from 'enzyme';
import { assert } from 'chai';
import DataCard from './index';

describe('<DataCard />', () => {
    describe('render', () => {
        it('renders properly if all props provided', () => {
            const fn = () => {};
            const data = [];
            const message = "";
            const wrapper = shallow(
              <DataCard
                cards = {data}
                message = {message}
                fetchCards = {fn}
                annotateCard = {fn}
                passCard={fn}
                unassignCard={fn}
              />
            );
        });
    });
});
