/* eslint-disable no-undef */
import './utils/jquery.formset.js';

import 'd3';
import 'nvd3';

import { getCookie } from './utils/fetch_configs.js';
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
            // Only send the token to relative URLs i.e. locally.
            xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
        }
    }
});
