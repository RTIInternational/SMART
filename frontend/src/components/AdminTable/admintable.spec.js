import React, {Component} from 'react';
import { shallow } from 'enzyme';
import { assert } from 'chai';
import AdminTable from './index';

describe('<AdminTable />', () => {
    describe('render', () => {
        it('renders properly if all props provided', () => {
            const fn = () => {};
            const data = [];
            const labels = [];

            const wrapper = shallow(
                <AdminTable
                  getAdmin = {fn}
                  admin_data={data}
                  labels={labels}
                  adminLabel = {fn}
                  discardData = {fn}
                />
            );
        });
    });
});
