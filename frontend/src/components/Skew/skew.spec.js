import React, {Component} from 'react';
import { shallow } from 'enzyme';
import { assert } from 'chai';
import Skew from './index';

describe('<Skew />', () => {
    describe('render', () => {
        it('renders properly if all props provided', () => {
            const fn = () => {};
            const data = [];
            const labels = [];

            const wrapper = shallow(
                <Skew
                  getUnlabeled = {fn}
                  unlabeled_data={data}
                  labels={labels}
                  skewLabel={fn}
                  getLabelCounts={fn}
                  label_counts={data}
                />
            );
        });
    });
});
