import React, { Component } from 'react';
import { shallow } from 'enzyme';
import { assert } from 'chai';
import Login from './index';

describe('<Login />', () => {
    describe('render', () => {
        it('renders properly with required props', () => {
            const wrapper = shallow(<Login login={() => {}} />);
        });
    });
});
