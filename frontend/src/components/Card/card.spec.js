import React, { Component } from 'react';
import { shallow } from 'enzyme';
import { assert } from 'chai';
import Card from './index';

describe('<Card />', () => {
    describe('render', () => {
        it('renders properly', () => {
            const wrapper = shallow(<Card />);
        });
    });

    describe('props', () => {
        it('should be able to accept classes', () => {
            const wrapper = shallow(
                <Card className="full" />
            );
            
            const { className } = wrapper.props();
            assert.strictEqual(className, "card full");
        });

        it('should be able to accept styles', () => {
            const styleProp = {
                'background-color': 'red'
            };

            const wrapper = shallow(
                <Card style={styleProp} />
            );

            const { style } = wrapper.props();
            assert.strictEqual(style, styleProp);
        });

        it('should be able to accept any children', () => {
            const child = <div foo="bar" />;
            
            const wrapper = shallow(
                <Card>
                    {child}
                </Card>
            );
            
            assert.strictEqual(wrapper.contains(child), true);
        });
    });
});
