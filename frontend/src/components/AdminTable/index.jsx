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
    accessor: "data",
    filterMethod: (filter, row) => {
      const id = filter.pivotId || filter.id;
      return row[id] !== undefined ? String(row[id]).toLowerCase().includes(filter.value.toLowerCase()) : true
    }
  }
];


class AdminTable extends React.Component {

  componentWillMount() {
      this.props.getAdmin();
  }

  render() {
  const {admin_data, labels, adminLabel} = this.props;
  if(admin_data)
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
        SubComponent={
          row => {
          return (
            <div>
            <p>{row.row.data}</p>
            {labels[0].map( (label) => (
              <Button key={label.id.toString() + "_" + row.row.id.toString()}
              onClick={() => adminLabel(row.row.id,label.id)}
              bsStyle="primary"
              >{label.name}</Button>
            ))}
            </div>
          );
        }}
        filterable={true}
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
