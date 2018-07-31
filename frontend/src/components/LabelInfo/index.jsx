import React from 'react';
import PropTypes from 'prop-types';
import {Button, Glyphicon} from "react-bootstrap";

class LabelInfo extends React.Component {

  render() {
  const {labels, labels_open} = this.props;

  if(labels_open)
  {
    return (
      <div className="margin-bottom-15">
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
      </div>
    )
  }
  else {
    return (
      <div className="margin-bottom-15">
      </div>
    )
  }

  }

}


LabelInfo.propTypes = {
  labels: PropTypes.arrayOf(PropTypes.object),
  labels_open: PropTypes.bool
};

export default LabelInfo;
