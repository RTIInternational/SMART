import React from 'react';
import PropTypes from 'prop-types';

class LabelInfo extends React.Component {

  render() {
  const {labels, labels_open} = this.props;

  if(labels_open)
  {
    return (
      <div className="row">
        <div className="col-md-12">
          <ul className="list-group-flush">
            {labels.map( (label) => (
              <li className="list-group-item" key={label.pk}>
                <dt>{label.name}</dt>
                <dd>{label.description}</dd>
              </li>
            ))}
          </ul>
        </div>
      </div>
    )
  }
  else {
    return null;
  }

  }

}


LabelInfo.propTypes = {
  labels: PropTypes.arrayOf(PropTypes.object),
  labels_open: PropTypes.bool
};

export default LabelInfo;
