import React from 'react';
import { connect } from 'react-redux';

import CodebookLabelMenu from '../components/CodebookLabelMenu';

console.log("CodebookLabelMenu::", CodebookLabelMenu);

const CodebookLabelMenuContainer = (props) => <CodebookLabelMenu {...props} />;

const mapStateToProps = (state) => {
    return {
        labels: state.card.labels
    };
};

export default connect(mapStateToProps)(CodebookLabelMenuContainer);
