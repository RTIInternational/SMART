import React, { Component } from 'react';
import { shallow } from 'enzyme';
import { assert } from 'chai';
import Smart from './index';

describe('<Smart />', () => {
    describe('render', () => {
        it('renders properly if all props provided', () => {
            const fn = () => {};
            const data = [];
            const message = "";
            const wrapper = shallow(
              <Smart
                fetchCards = {fn}
                annotateCard = {fn}
                passCard =  {fn}
                popCard = {fn}
                cards =  {data}
                message = {message}
              />
            );
        });
    });
});
