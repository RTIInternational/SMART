import React, { Component } from 'react';
import { shallow } from 'enzyme';
import { assert } from 'chai';
import Smart from './index';

describe('<Smart />', () => {
    describe('render', () => {
        it('renders properly', () => {
            const wrapper = shallow(<Smart />);
        });
    });
});
