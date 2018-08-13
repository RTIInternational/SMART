import React, {Component} from 'react';
import { shallow } from 'enzyme';
import { assert } from 'chai';
import RecycleBinTable from './index';

describe('<RecycleBinTable />', () => {
    describe('render', () => {
        it('renders properly if all props provided', () => {
            const fn = () => {};
            const data = [];

            const wrapper = shallow(
                <RecycleBinTable
                  getDiscarded = {fn}
                  discarded_data = {data}
                  restoreData = {fn}
                  labels = {data}
                />
            );
        });
    });
});
