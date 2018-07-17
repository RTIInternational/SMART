import React from 'react';
import PropTypes from 'prop-types';
import ReactTable from 'react-table';
import {Button, ButtonToolbar} from "react-bootstrap";

class AdminTable extends React.Component {

  componentWillMount() {
      this.props.getAdmin();
  }

  render() {
  const {admin_data, labels, adminLabel} = this.props;

  if(labels && labels.length > 0)
  {
    var label_list = labels[0];
  }
  else {
    label_list = [];
  }

  if(admin_data && admin_data.length > 0)
  {
    var table_data = admin_data[0];
  }
  else {
    table_data = [];
  }

  var expanded = {}
  for(var i = 0; i < table_data.length; i++)
  {
    expanded[i] = true;
  }

  const columns = [
    {
      Header: "id",
      accessor: "id",
      show: false
    },
    {
      Header: "Unlabeled Data",
      accessor: "data",
      Cell: row => (
        <div>
          <p id="admin_text">{row.row.data}</p>
          <div id="admin_buttons">
          <ButtonToolbar bsClass="btn-toolbar pull-right">
            {label_list.map( (label) => (
              <Button key={label.id.toString() + "_" + row.row.id.toString()}
              onClick={() => adminLabel(row.row.id,label.id)}
              bsStyle="primary"
              >{label.name}</Button>
            ))}
          </ButtonToolbar>
          </div>
        </div>
      )
    }
  ];
  return (
    <div>
    <h3>Instructions</h3>
    <p>This page allows an admin to label data that was skipped by labelers.</p>
      <ReactTable
        data={table_data}
        columns={columns}
        pageSizeOptions={[1,5,10,20,30,50,100]}
        defaultPageSize={1}
        expanded={expanded}
        filterable={false}
      />
    </div>
  );
  }

}

AdminTable.propTypes = {
  getAdmin: PropTypes.func.isRequired,
  admin_data: PropTypes.arrayOf(PropTypes.object),
  labels: PropTypes.arrayOf(PropTypes.object),
  adminLabel: PropTypes.func.isRequired
};

export default AdminTable;
