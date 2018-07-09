import React from 'react';
import PropTypes from 'prop-types';
import ReactTable from 'react-table';
import { Button, Panel, Table } from "react-bootstrap";
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

  return (
    <div>
      <h3>Instructions</h3>
      <p>This page allows an admin to manually search for and annotate data in the case of a particularly bad data skew.</p>
      <p>To the left is a chart that shows the distribution of labels in the project. Below is all of the unlabeled data that are not in a queue.</p>
      <p>To annotate, click on a data entry below and select the label from the expanded list of labels. As you label data the chart to the left will update.</p>
      <Table>
        <tbody>
          <tr>
            <td className="col-md-5">
              <Panel>

                <NVD3Chart
                id="labelCounts"
                type="multiBarChart"
                datum={label_data}
                duration={300}
                groupSpacing={0.1}
                stacked={true}
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
            <td>
              <ReactTable
                data={unlabeled_data[0]}
                columns={columns}
                SubComponent={row => {
                  return (
                    <div>
                    <p>{row.row.data}</p>
                    {labels[0].map( (label) => (
                      <Button key={label.id.toString() + "_" + row.row.id.toString()}
                      onClick={() => skewLabel(row.row.id,label.id)}
                      bsStyle="primary"
                      >{label.name}</Button>
                    ))}
                    </div>
                  );
                }}
                filterable={true}
              />
            </td>
          </tr>
        </tbody>
      </Table>
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
