import React, { Component } from 'react';
import { shallow } from 'enzyme';
import { assert } from 'chai';
import SmartProgressBar from './index';

describe('<SmartProgressBar />', () => {
    describe('render', () => {
        it('renders properly if all props provided', () => {
            const fn = () => {};
            const data = [];
            const message = "";
            const wrapper = shallow(
              <SmartProgressBar
                cards = {data}
              />
            );
        });
    });
});
