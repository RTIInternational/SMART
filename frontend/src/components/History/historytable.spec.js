import React, {Component} from 'react';
import { shallow } from 'enzyme';
import { assert } from 'chai';
import History from './index';

describe('<History />', () => {
    describe('render', () => {
        it('renders properly if all props provided', () => {
            const fn = () => {};
            const data = [];
            const labels = [];

            const wrapper = shallow(
                <History
                  getHistory = {fn}
                  history_data={data}
                  changeLabel = {fn}
                  changeToSkip= {fn}
                  verifyDataLabel = {fn}
                  labels={labels}
                />
            );
        });
    });
});
