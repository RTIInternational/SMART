import React from 'react';
import { connect } from 'react-redux';

import { getDiscarded, restoreData } from '../actions/recycleBin';
import RecycleBin from '../components/RecycleBin';

const PROJECT_ID = window.PROJECT_ID;

const RecycleBinContainer = (props) => <RecycleBin {...props} />;

const mapStateToProps = (state) => {
    return {
        discarded_data: state.recycleBin.discarded_data,
        hasExplicit: state.smart.hasExplicit
    };
};

const mapDispatchToProps = (dispatch) => {
    return {
        restoreData: (dataID) => {
            dispatch(restoreData(dataID, PROJECT_ID));
        },
        getDiscarded: () => {
            dispatch(getDiscarded(PROJECT_ID));
        }
    };
};

export default connect(mapStateToProps, mapDispatchToProps)(RecycleBinContainer);
