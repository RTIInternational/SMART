import React, {Component} from 'react';
import { shallow } from 'enzyme';
import { assert } from 'chai';
import RecycleBin from './index';

describe('<RecycleBin />', () => {
    describe('render', () => {
        it('renders properly if all props provided', () => {
            const fn = () => {};
            const data = [];

            const wrapper = shallow(
                <RecycleBin
                  getDiscarded = {fn}
                  discarded_data = {data}
                  restoreData = {fn}
                />
            );
        });
    });
});
