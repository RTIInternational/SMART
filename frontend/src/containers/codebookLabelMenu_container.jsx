import React from 'react';
import { connect } from 'react-redux';

import CodebookLabelMenu from '../components/CodebookLabelMenu';


const CodebookLabelMenuContainer = (props) => <CodebookLabelMenu {...props} />;

const mapStateToProps = (state) => {
    return {
        labels: state.card.labels
    };
};

const mapDispatchToProps = (dispatch) => {
    return {
    };
};

export default connect(mapStateToProps, mapDispatchToProps)(CodebookLabelMenuContainer);
