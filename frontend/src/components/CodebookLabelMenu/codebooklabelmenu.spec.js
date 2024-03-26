import React, { Component } from 'react';
import { shallow } from 'enzyme';
import { assert } from 'chai';
import CodebookLabelMenu from './index';

describe('<CodebookLabelMenu />', () => {
    describe('render', () => {
        it('renders properly if all props provided', () => {
            const labels = [];
            const wrapper = shallow(
                <CodebookLabelMenu /> 
            );
        });
    });
});
