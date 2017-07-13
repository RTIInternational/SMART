import React, { Component } from 'react';
import { shallow } from 'enzyme';
import { assert } from 'chai';
import Header from './index';

describe('<Header />', () => {
    describe('render', () => {
        it('renders properly', () => {
            const wrapper = shallow(<Header />);
        });
    });

    describe('props', () => {
        it('should be able to accept any children', () => {
            const child = <div foo="bar" />;
            
            const wrapper = shallow(
                <Header>
                    {child}
                </Header>
            );
            
            assert.strictEqual(wrapper.contains(child), true);
        });
    });
});
