import React from 'react';
import PropTypes from 'prop-types';
import {Button, Glyphicon} from "react-bootstrap";

class LabelInfo extends React.Component {
  constructor(props)
  {
    super(props);
    this.state= {
      labels_open: false
    };
    this.toggleLabel = this.toggleLabel.bind(this);
  }

  toggleLabel(){ this.setState({labels_open: !this.state.labels_open})};

  render() {
  const {labels} = this.props;

  if(this.state.labels_open)
  {
    return (
      <div className="margin-bottom-15">
        <Button
        bsSize="small"
        onClick={this.toggleLabel}
        className="minus_button"
        bsStyle="danger"
        >
        <Glyphicon glyph="minus"/> Label Guide
        </Button>
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
        <Button
        bsSize="small"
        onClick={this.toggleLabel}
        className="plus_button"
        bsStyle="success"
        >
        <Glyphicon glyph="plus"/> Label Guide
        </Button>
      </div>
    )
  }

  }

}


LabelInfo.propTypes = {
  labels: PropTypes.arrayOf(PropTypes.object)
};

export default LabelInfo;
