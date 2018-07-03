import React from 'react';
import PropTypes from 'prop-types';
import ReactTable from 'react-table';
import {Button} from "react-bootstrap";
const columns = [
  {
    Header: "id",
    accessor: "id"
  },
  {
    Header: "Data",
    accessor: "data"
  },
  {
    Header: "Old Label",
    accessor: "old_label"
  },
  {
    Header: "Old Label ID",
    accessor: "old_label_id"
  },
  {
    Header: "Date/Time",
    accessor: "timestamp"
  }
];


class HistoryTable extends React.Component {

  componentWillMount() {
      this.props.getHistory();
  }


  render() {
  const {getHistory, history_data, labels, changeLabel} = this.props;
  return (
    <div>
      <ReactTable
        data={this.props.history_data[0]}
        columns={columns}
        SubComponent={row => {
          return (
            <div>{labels[0].map( (label) => (
              <Button key={label.id.toString() + "_" + row.row.id.toString()}
              onClick={() => changeLabel(row.row.id,row.row.old_label_id,label.id)}>{label.name}</Button>
            ))}</div>
          );
        }}
      />
    </div>
  )
  }

}


//This component will have
// change label (action)
// change_to_skip (action)
// data
HistoryTable.propTypes = {
  getHistory: PropTypes.func.isRequired,
  history_data: PropTypes.arrayOf(PropTypes.object),
  labels: PropTypes.arrayOf(PropTypes.object),
  changeLabel: PropTypes.func.isRequired
};

export default HistoryTable;
