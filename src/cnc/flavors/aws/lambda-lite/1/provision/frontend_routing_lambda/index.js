'use strict';

exports.handler = async (event, context, callback) => {
    const cf = event.Records[0].cf;
    const request = cf.request;
    const response = cf.response;
    const statusCode = response.status;

    if (statusCode == '404') {
        response.status = '200'
    }

    console.log('response: ' + JSON.stringify(response));
    callback(null, response);
    return response;
};
