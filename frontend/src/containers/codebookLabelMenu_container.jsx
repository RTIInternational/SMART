import React from 'react';
import { connect } from 'react-redux';

import CodebookLabelMenu from '../components/CodebookLabelMenu';

const CODEBOOK_URL = window.CODEBOOK_URL;

const CodebookLabelMenuContainer = (props) => {
    if (CODEBOOK_URL != "") {
        return (<CodebookLabelMenu {...props} />);
    } else {
        return (<div></div>);
    }

};

const mapStateToProps = (state) => {
    return {};
};

export default connect(mapStateToProps)(CodebookLabelMenuContainer);
