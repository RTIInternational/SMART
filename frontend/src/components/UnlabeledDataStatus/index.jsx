import React from "react";
import PropTypes from "prop-types";

class UnlabeledDataStatus extends React.Component {
    componentDidMount() {
        this.props.getUnlabeled();
    }

    render() {
        const { unlabeled_data } = this.props;

        console.log(this.props);
        return (
            <p className="unlabeled-status">
                Unlabeled Outstanding: {unlabeled_data.length}
            </p>
        );
    }
}

//This component will have
// unlabeled data
// accessor
UnlabeledDataStatus.propTypes = {
    getUnlabeled: PropTypes.func.isRequired,
    unlabeled_data: PropTypes.arrayOf(PropTypes.object)
};

export default UnlabeledDataStatus;
