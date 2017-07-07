import React, {Component} from 'react';
import {shallow} from 'enzyme';
import {assert} from 'chai';
import Wrapper from './wrapper';

describe('<Wrapper />', () => {
    describe('prop: children', () => {
        it('should be able to accept any children', () => {
            const child = <div foo="bar" />;
            
            const wrapper = shallow(
                <Wrapper>
                    {child}
                </Wrapper>
            );
            
            assert.strictEqual(wrapper.contains(child), true);
        });
    });
});