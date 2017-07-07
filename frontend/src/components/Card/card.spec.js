import React, {Component} from 'react';
import {shallow} from 'enzyme';
import {assert} from 'chai';
import Card from './card';

describe('<Card />', () => {
    describe('prop: children', () => {
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