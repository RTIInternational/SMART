import React from 'react';
import { connect } from 'react-redux';
import HistoryTable from '../components/History/HistoryTable';

const HistoryContainer = (props) => <HistoryTable {...props} />;

const mapStateToProps = (state) => {
    return {};
};

const mapDispatchToProps = (dispatch) => {
    return {};
};

export default connect(mapStateToProps, mapDispatchToProps)(HistoryContainer);
