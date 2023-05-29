import React from 'react';
import { connect } from 'react-redux';

import CodebookLabelMenu from '../components/CodebookLabelMenu';

const CodebookLabelMenuContainer = (props) => <CodebookLabelMenu {...props} />;

const mapStateToProps = (state) => {
    return {
        labels: state.smart.labels
    };
};

export default connect(mapStateToProps)(CodebookLabelMenuContainer);
