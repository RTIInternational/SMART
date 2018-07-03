import React, {Component} from 'react';
import { shallow } from 'enzyme';
import { assert } from 'chai';
import HistoryTable from './index';

describe('<HistoryTable />', () => {
    describe('render', () => {
        it('renders properly if all props provided', () => {
            const fn = () => {};
            const data = [];
            const labels = [];

            const wrapper = shallow(
                <HistoryTable
                  getHistory = {fn}
                  history_data={data}
                  labels={labels}
                  changeLabel = {fn}
                />
            );
        });
    });
});
