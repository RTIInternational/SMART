import { createAction } from 'redux-actions';
import 'whatwg-fetch';

import { getConfig, postConfig } from '../utils/fetch_configs';
import {setMessage} from './classifier'
import { getLabelCounts } from './adminTables'
export const SET_HIST_DATA = 'SET_HIST_DATA';
export const SET_LABELS = 'SET_LABELS';

export const set_hist_data = createAction(SET_HIST_DATA);
export const set_labels = createAction(SET_LABELS);
//Get the data for the history table
export const getHistory = (projectID) => {
  let apiURL = `/api/get_label_history/${projectID}/`;
  return dispatch => {
    return fetch(apiURL, getConfig())
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            else {
                const error = new Error(response.statusText)
                error.response = response;
                throw error;
            }
        })
        .then(response => {
            // If error was in the response then set that message
            if ('error' in response) console.log(response);
            var all_labels = []
            for (let i = 0; i < response.labels.length; i++) {
                const label = {"id":response.labels[i].pk, "name":response.labels[i].name};
                all_labels.push(label);
            }
            dispatch(set_labels(all_labels));
            var all_data = [];
            for (let i = 0; i < response.data.length; i++) {
                const row = {
                    id: response.data[i].id,
                    data: response.data[i].data,
                    old_label: response.data[i].label,
                    old_label_id: response.data[i].labelID,
                    timestamp: response.data[i].timestamp
                }
                all_data.push(row);
            }
            dispatch(set_hist_data(all_data));
        })
        .catch(err => console.log("Error: ", err));
  }
};


export const changeLabel = (dataID, oldLabelID, labelID, projectID) => {
  let payload = {
    dataID: dataID,
    oldLabelID: oldLabelID,
    labelID: labelID
  }
  let apiURL = `/api/modify_label/${dataID}/`;
  return dispatch => {
      return fetch(apiURL, postConfig(payload))
          .then(response => {
              if (response.ok) {
                  return response.json();
              }
              else {
                  const error = new Error(response.statusText)
                  error.response = response;
                  throw error;
              }
          })
          .then(response => {
              if ('error' in response) {
                  return dispatch(setMessage(response.error))
              }
              else {
                  dispatch(getHistory(projectID))
                  dispatch(getLabelCounts(projectID))
              }
          })
  }
};

export const changeToSkip = (dataID, oldLabelID, projectID) => {
  let payload = {
    dataID: dataID,
    oldLabelID: oldLabelID,
  }
  let apiURL = `/api/modify_label_to_skip/${dataID}/`;
  return dispatch => {
      return fetch(apiURL, postConfig(payload))
          .then(response => {
              if (response.ok) {
                  return response.json();
              }
              else {
                  const error = new Error(response.statusText)
                  error.response = response;
                  throw error;
              }
          })
          .then(response => {
              if ('error' in response) {
                  return dispatch(setMessage(response.error))
              }
              else {
                  dispatch(getHistory(projectID))
              }
          })
  }
};
