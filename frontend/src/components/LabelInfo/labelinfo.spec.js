import React, { Component } from 'react';
import { shallow } from 'enzyme';
import { assert } from 'chai';
import LabelInfo from './index';

describe('<LabelInfo />', () => {
    describe('render', () => {
        it('renders properly if all props provided', () => {
            const labels = [];
            const wrapper = shallow(
                <LabelInfo
                    labels={labels}
                    labels_open={true}
                />
            );
        });
    });
});
