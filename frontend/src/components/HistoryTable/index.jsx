import React from 'react';
import PropTypes from 'prop-types';
import ReactTable from 'react-table';
import {Button, ButtonToolbar} from "react-bootstrap";

const columns = [
  {
    Header: "edit",
    accessor: "edit",
    show: false
  },
  {
    Header: "id",
    accessor: "id",
    show: false
  },
  {
    Header: "Data",
    accessor: "data",
    filterMethod: (filter, row) => {
      if(String(row["data"]).toLowerCase().includes(filter.value.toLowerCase()))
      {
        return true;
      }
      else {
        return false;
      }
    }
  },
  {
    Header: "Old Label",
    accessor: "old_label",
    width: 100
  },
  {
    Header: "Old Label ID",
    accessor: "old_label_id",
    show: false
  },
  {
    Header: "Date/Time",
    accessor: "timestamp",
    id: "timestamp",
    width: 150
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
          if(row.row.edit === "yes")
          {
            return (
              <div className="sub-row">
                <p>{row.row.data}</p>
                <ButtonToolbar bsClass="btn-toolbar pull-right">
                  {labels.map( (label) => (
                    <Button key={label.pk.toString() + "_" + row.row.id.toString()}
                    onClick={() => {
                      if(!(row.row.old_label_id === label.pk))
                      {
                        changeLabel(row.row.id,row.row.old_label_id,label.pk)
                      }
                    }}
                    bsStyle="primary"
                    >{label.name}</Button>
                  ))}
                  <Button onClick={() => changeToSkip(row.row.id,row.row.old_label_id)}
                  bsStyle="info"
                  >Skip</Button>
                </ButtonToolbar>
              </div>
            );
          }
          else {
            return (
              <div className="sub-row">
                <p>{row.row.data}</p>
                <p id="irr_history_message">Note: This is Inter-rater Reliability data and is not editable.</p>
              </div>
            );
          }
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
