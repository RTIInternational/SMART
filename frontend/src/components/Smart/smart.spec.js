import React, { Component } from 'react';
import { shallow } from 'enzyme';
import { assert } from 'chai';
import Smart from './index';

describe('<Smart />', () => {
    describe('render', () => {
        it('renders properly if all props provided', () => {
            const fn = () => {};
            const data = [];
            const message = "";
            const wrapper = shallow(
              <Smart
                cards =  {data}
                message = {message}
                adminTabsAvailable = {false}
                getAdminTabsAvailable = {fn}
                fetchCards = {fn}
                annotateCard = {fn}
                passCard =  {fn}
                popCard = {fn}
                admin_counts = {data}
                getAdminCounts = {fn}
              />
            );
        });
    });
});
