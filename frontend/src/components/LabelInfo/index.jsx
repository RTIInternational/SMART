import React from 'react';
import PropTypes from 'prop-types';
import ReactTable from 'react-table';
import {Button, Glyphicon} from "react-bootstrap";

const label_columns = [
  {
    Header: "id",
    accessor: "id",
    show: false
  },
  {
    Header: "Label",
    accessor: "name",
    filterMethod: (filter, row) => {
      if(String(row["name"]).toLowerCase().includes(filter.value.toLowerCase()))
      {
        return true;
      }
      else {
        return false;
      }
    }
  },
  {
    Header: "Description",
    accessor: "description",
    className: "no_word_wrap",
    filterMethod: (filter, row) => {
      if(String(row["description"]).toLowerCase().includes(filter.value.toLowerCase()))
      {
        return true;
      }
      else {
        return false;
      }
    }

  }
];

class LabelInfo extends React.Component {
  constructor(props)
  {
    super(props);
    this.state= {
      labels_open: false
    };
    this.toggleLabel = this.toggleLabel.bind(this);
  }

  componentWillMount() {
      this.props.getLabels();
  }

  toggleLabel(){ this.setState({labels_open: !this.state.labels_open})};

  render() {
  const {labels} = this.props;

  if(this.state.labels_open)
  {
    return (
      <div>
        <Button
        bsSize="small"
        onClick={this.toggleLabel}
        className="minus_button"
        bsStyle="danger"
        >
        <Glyphicon glyph="minus"/> Label Guide
        </Button>
        <ReactTable
          data={labels[0]}
          columns={label_columns}
          filterable={true}
          minRows={2}
          className="label_table"
        />
      </div>
    )
  }
  else {
    return (<Button
    bsSize="small"
    onClick={this.toggleLabel}
    className="plus_button"
    bsStyle="success"
    >
    <Glyphicon glyph="plus"/> Label Guide
    </Button>)
  }

  }

}


LabelInfo.propTypes = {
  getLabels: PropTypes.func.isRequired,
  labels: PropTypes.arrayOf(PropTypes.object)
};

export default LabelInfo;
