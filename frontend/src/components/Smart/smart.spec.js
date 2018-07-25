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
                history_data = {data}
                getHistory = {fn}
                changeLabel = {fn}
                changeToSkip = {fn}
                getUnlabeled = {fn}
                unlabeled_data = {data}
                label_counts = {data}
                skewLabel = {fn}
                getLabelCounts = {fn}
                getAdmin = {fn}
                admin_data = {data}
                adminLabel = {fn}
                fetchCards = {fn}
                annotateCard = {fn}
                passCard =  {fn}
                popCard = {fn}
                cards =  {data}
                message = {message}
              />
            );
        });
    });
});
