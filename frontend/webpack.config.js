/* eslint-disable */
var webpack = require('webpack');
var path = require('path');

var release = (process.env.NODE_ENV === 'production');

var CleanWebpackPlugin = require('clean-webpack-plugin');
var HtmlWebpackPlugin = require('html-webpack-plugin');
var ExtractTextPlugin = require("extract-text-webpack-plugin");
var OptimizeCssAssetsPlugin = require('optimize-css-assets-webpack-plugin');
var StyleLintPlugin = require('stylelint-webpack-plugin');
var BundleTracker = require('webpack-bundle-tracker');

var config = {
    context: path.join(__dirname, "src"),
    devServer: {
        contentBase: path.join(__dirname, "dist"),
        port: 3000,
        host: "0.0.0.0"
    },
    devtool: release ? 'source-map' : 'eval-source-map',
    entry: {
        smart: './smart.jsx',
        vendor: [
            'react',
            'react-dom',
            'react-redux',
            'redux'
        ]
    },
    module: {
        rules: [
            {
                test: /\.jsx?$/,
                exclude: /node_modules/,
                use: [
                    'babel-loader',
                    'eslint-loader'
                ]
            },
            {
                test: /\.(jpe?g|gif|html)$/,
                use: [
                    {
                        loader: 'file-loader',
                        options: {
                            name: "[name].[ext]"
                        }
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
    output: {
         path: path.resolve(__dirname, 'dist')
    },
    plugins: [
        new BundleTracker({ filename: './webpack-stats.json' }),
        new StyleLintPlugin({
            context: './src/styles/'
        })
    ],
    performance: {
        assetFilter: function(assetFilename) {
            return assetFilename.endsWith('.js') || assetFilename.endsWith('.css');
        },
        hints: "warning",
        maxEntrypointSize: 1000000
    },
    profile: true,
    resolve: {
        modules: [
            'node_modules',
            path.join(__dirname, "src")
        ],
        extensions: ['.js', '.jsx'],
    }
}

if (release) {
    config.output.filename = '[name].[hash].js';
    config.output.chunkFilename = '[name].[hash].js';

    config.module.rules.push(
        {
            test: /\.css$/,
            use: ExtractTextPlugin.extract({
                fallback: "style-loader",
                use: "css-loader"
            })
        },
        {
            test: /\.scss$/,
            use: ExtractTextPlugin.extract({
                fallback: "style-loader",
                use: [
                    {
                        loader: 'css-loader',
                        options: {
                            sourceMap: true,
                        }
                    },
                    {
                        loader: 'resolve-url-loader',
                        options: {
                            sourceMap: true,
                            keepQuery: true
                        }
                    },
                    {
                        loader: 'sass-loader',
                        options: {
                            sourceMap: true,
                            outputStyle: "compress"
                        }
                    }
                ]
            })
        }
    );

    config.plugins.push(
        new CleanWebpackPlugin(['dist'], {
          root: path.resolve(),
          verbose: true,
          dry: false
        }),
        new webpack.DefinePlugin({
            'DEBUG': false,
            'PRODUCTION': true,
            'process.env.NODE_ENV': JSON.stringify('production')
        }),
        new ExtractTextPlugin({ filename: '[name].[contenthash].css', allChunks: true }),
        new OptimizeCssAssetsPlugin({
          cssProcessor: require('cssnano'),
          cssProcessorOptions: {
              discardComments: {
                  removeAll: true
              }
          },
          canPrint: false
        }),
        new webpack.optimize.AggressiveMergingPlugin(),
        new webpack.optimize.OccurrenceOrderPlugin(),
        new webpack.optimize.UglifyJsPlugin({
            mangle: true,
            compress: {
                warnings: false,
                pure_getters: true,
                unsafe_comps: true,
                screw_ie8: true
            },
            output: {
                comments: false,
            },
            exclude: [/\.min\.js$/gi],
            sourceMap: true
        }),
        new webpack.LoaderOptionsPlugin({
            minimize: true,
            debug: false
        }),
        new webpack.optimize.CommonsChunkPlugin({
            name: 'vendor',
            minChunks: function (module) {
               return module.context && module.context.indexOf('node_modules') !== -1;
            }
        }),
        new webpack.optimize.CommonsChunkPlugin({
            name: "manifest",
            minChunks: Infinity
        }),
        new HtmlWebpackPlugin({
            cache: false,
            filename: 'index.html',
            template: 'index.ejs',
            minify: {
                collapseWhitespace: true,
                html5: true,
                removeComments: true,
                removeRedundantAttributes: true,
                removeScriptTypeAttributes: true,
                removeStyleLinkTypeAttributes: true
            }
        })
    );
} else {
    config.output.filename = '[name].js';
    config.module.rules.push(
        {
            test: /\.css$/,
            use: [
                {
                    loader: 'style-loader'
                },
                {
                    loader: 'css-loader'
                }
            ]
        },
        {
            test: /\.scss$/,
            use: [
                {
                    loader: 'style-loader'
                },
                {
                    loader: 'css-loader'
                },
                {
                    loader: 'resolve-url-loader',
                    options: {
                        sourceMap: true,
                        keepQuery: true
                    }
                },
                {
                    loader: 'sass-loader',
                    options: {
                        sourceMap: true,
                    }
                }
            ]
        }
    );

    config.plugins.push(
        new webpack.DefinePlugin({
            'DEBUG': true,
            'PRODUCTION': false
        }),
        new HtmlWebpackPlugin({
            cache: false,
            filename: 'index.html',
            template: 'index.ejs'
        })
    );
}

module.exports = config;