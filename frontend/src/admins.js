import $ from 'jquery';
import dt from 'datatables.net-bs';
import 'bootstrap';
dt(window, $);


/* eslint-disable no-unused-vars */
const PROJECT_PK = window.PROJECT_PK;
const PROJECT_CLASSIFIER = window.PROJECT_CLASSIFIER;
const PROJECT_LEARNING_METHOD = window.PROJECT_LEARNING_METHOD;
const PROJECT_PERCENTAGE_IRR = window.PROJECT_PERCENTAGE_IRR;
/* eslint-enable no-unused-vars */

import './utils/admin_label.js';
import './utils/admin_model.js';
import './utils/admin_irr.js';

$(document).ready(function() {
    $(function () {
        $('[data-toggle="tooltip"]').tooltip();
    });

});

/*
 *  Force window resize event when bootstrap tab navigation anchor is used
 *  This is needed because nvd3 charts are incorrectly sized if they are
 *  initially rendered while hidden.
 */
$(function () {
    $(document).on('shown.bs.tab', 'a[data-toggle="tab"]', function () {
        window.dispatchEvent(new Event('resize'));
    });
});
