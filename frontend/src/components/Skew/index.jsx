import React from 'react';
import PropTypes from 'prop-types';
import ReactTable from 'react-table';
import { Button, ButtonToolbar, Panel, Table } from "react-bootstrap";
import NVD3Chart from "react-nvd3";
import d3 from 'd3';

const columns = [
  {
    Header: "id",
    accessor: "id",
    show: false
  },
  {
    Header: "Unlabeled Data",
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
  }
];

class Skew extends React.Component {
  constructor(props)
  {
    super(props);
  }


  componentWillMount() {
      this.props.getUnlabeled();
      this.props.getLabelCounts();
  }


  render() {

  const {unlabeled_data, labels, skewLabel, label_counts} = this.props;


  var label_data = [];
  if(label_counts.length > 0)
  {
    label_data = label_counts[0];
  }
  if(unlabeled_data && unlabeled_data.length > 0)
  {
    var table_data = unlabeled_data[0]
  }
  else {
    table_data = []
  }
  var page_sizes = [1];
  var counter = 1;
  for(var i = 5; i < table_data.length; i+=5*counter)
  {
    page_sizes.push(i);
    counter +=1;
  }
  page_sizes.push(table_data.length);

  return (
    <div>
    <Table id="skew_table">
      <tbody>
        <tr>
          <td className="col-md-4">
            <h3>Instructions</h3>
            <p>This page allows an admin to manually search for and annotate data in the case of a particularly bad data skew.</p>
            <p>To the left is a chart that shows the distribution of labels in the project. Below is all of the unlabeled data that are not in a queue.</p>
            <p>To annotate, click on a data entry below and select the label from the expanded list of labels. As you label data the chart to the left will update.</p>
          </td>
          <td className="col-md-4">
            <Panel id="chart_panel">
              <NVD3Chart
              id="label_counts"
              type="multiBarChart"
              datum={label_data}
              duration={300}
              groupSpacing={0.1}
              stacked={true}
              height={300}
              yAxis={{
                axisLabel: "Number of Data Annotated",
                axisLabelDistance: -5,
                tickFormat: d3.format(',.01f')
              }}
              xAxis={{
                axisLabel: "Label",
                axisLabelDistance: 15,
                showMaxMin: false
              }}
              noData="Insufficient labeled data -- please code more documents"
              margin={{
                bottom: 20,
                left: 70
              }}
              />
            </Panel>
          </td>
        </tr>
      </tbody>
    </Table>
    <ReactTable
        data={table_data}
        columns={columns}
        filterable={true}
        pageSizeOptions={page_sizes}
        SubComponent={row => {
          return (
            <div className="sub-row">
              <p id="skew_text">{row.row.data}</p>
              <div id="skew_buttons">
                <ButtonToolbar bsClass="btn-toolbar pull-right">
                  {labels.map( (label) => (
                    <Button key={label.pk.toString() + "_skew_" + row.row.id.toString()}
                    onClick={() => skewLabel(row.row.id,label.pk)}
                    bsStyle="primary"
                    >{label.name}</Button>
                  ))}
                </ButtonToolbar>
              </div>
            </div>
          );
        }}
    />
  </div>
  )
  }

}


//This component will have
//data for the table
//data for the graph
//accessors for both
Skew.propTypes = {
  getUnlabeled: PropTypes.func.isRequired,
  unlabeled_data: PropTypes.arrayOf(PropTypes.object),
  labels: PropTypes.arrayOf(PropTypes.object),
  skewLabel: PropTypes.func.isRequired,
  getLabelCounts: PropTypes.func.isRequired,
  label_counts: PropTypes.arrayOf(PropTypes.object)
};

export default Skew;
