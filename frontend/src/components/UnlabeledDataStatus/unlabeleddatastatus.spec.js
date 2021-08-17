import React from 'react';
import { shallow } from 'enzyme';
import UnlabeledDataStatus from './index';

describe('<UnlabeledDataStatus />', () => {
    describe('render', () => {
        it('renders properly if all props provided', () => {
            const fn = () => {};
            const data = [];
            const wrapper = shallow(
                <UnlabeledDataStatus
                    getUnlabeled = {fn}
                    unlabeled_data={data}
                /> 
            );
        });
    });
});
