import React from 'react';
import PropTypes from 'prop-types';
import ReactTable from 'react-table';
import {Button} from "react-bootstrap";

const columns = [
  {
    Header: "id",
    accessor: "id",
    show: false
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
    accessor: "old_label_id",
    show: false
  },
  {
    Header: "Date/Time",
    accessor: "timestamp",
    id: "timestamp"
  }
];


class HistoryTable extends React.Component {

  componentWillMount() {
      this.props.getHistory();
  }


  render() {
  const {history_data, labels, changeLabel, changeToSkip} = this.props;
  return (
    <div>
    <h3>Instructions</h3>
    <p>This page allows a coder to change past labels.</p>
    <p>To annotate, click on a data entry below and select the label from the expanded list of labels. The chart will then update with the new label and current timestamp </p>
    <p><strong>NOTE:</strong> Data labels that are changed on this page will not effect past model accuracy or data selected by active learning in the past. The training data will only be updated for the next run of the model</p>
      <ReactTable
        data={history_data[0]}
        columns={columns}
        SubComponent={row => {
          return (
            <div>
            <p>{row.row.data}</p>
            {labels[0].map( (label) => (
              <Button key={label.id.toString() + "_" + row.row.id.toString()}
              onClick={() => changeLabel(row.row.id,row.row.old_label_id,label.id)}>{label.name}</Button>
            ))}
            <Button onClick={() => changeToSkip(row.row.id,row.row.old_label_id)}>Skip</Button>
            </div>
          );
        }}
        filterable={true}
        defaultSorted={[{
          id: "timestamp",
          desc: true
        }]}

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
  changeLabel: PropTypes.func.isRequired,
  changeToSkip: PropTypes.func.isRequired
};

export default HistoryTable;
