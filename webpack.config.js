/* eslint-disable */
var path = require('path');
var webpack = require('webpack');
var BundleTracker = require('webpack-bundle-tracker');

module.exports = {
    context: __dirname,

    entry: './assets/js/index.js',

    output: {
        path: path.resolve('./assets/bundles/'),
        filename: "[name]-[hash].js"
    },

    plugins: [
        new BundleTracker({ filename: './webpack-stats.json' }),
    ],

    profile: true,

    module: {
        rules: [
            {
                test: /\.jsx?$/,
                exclude: /node_modules/,
                use: [
                    { loader: 'babel-loader',
                      options: {
                          presets: ["es2015", "react"]
                      }
                    }
                ]
            },
            {
                test: /\.css$/,
                use: [
                    { loader: 'style-loader' },
                    { loader: 'css-loader' },
                ]
            },
            {
                test: /\.scss$/,
                use: [
                    { loader: 'style-loader' },
                    { loader: 'css-loader' },
                    { loader: 'resolve-url-loader',
                      options: {
                          sourceMap: true,
                          keepQuery: true
                      }
                    },
                    { loader: 'sass-loader',
                      options: {
                          sourceMap: true
                      }
                    }
                ]
            },
            {
                test: /\.(jpe?g|gif|html)$/,
                use: [
                    { loader: 'file-loader',
                      options: { name: "[name].[ext]" }
                    }
                ]
            },
            {
                test: /\.(png|ttf|eot|svg|woff(2)?)(\?[a-zA-Z0-9=.]+)?$/,
                use: [
                    { loader: 'url-loader',
                      options: {
                          limit: 10000,
                          name: "[name].[ext]"
                      }
                    }
                ]
            }
        ]
    },

    resolve: {
        modules: ['node_modules'],
        extensions: ['.js', '.jsx']
    }
}
