/* eslint-disable */
var webpack = require('webpack');
var path = require('path');

var release = (process.env.NODE_ENV === 'production');

var CleanWebpackPlugin = require('clean-webpack-plugin');
var ExtractTextPlugin = require("extract-text-webpack-plugin");
var OptimizeCssAssetsPlugin = require('optimize-css-assets-webpack-plugin');
var StyleLintPlugin = require('stylelint-webpack-plugin');
var BundleTracker = require('webpack-bundle-tracker');

var config = {
    context: path.join(__dirname, "src"),
    devtool: 'source-map',
    entry: {
        smart: './smart.jsx',
        globals: './globals.js'
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
                                outputStyle: release ? "compress" : "expanded"
                            }
                        }
                    ]
                }),
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
            },
            {
                test: /\.css$/,
                use: ExtractTextPlugin.extract({
                    fallback: "style-loader",
                    use: "css-loader"
                })
            },
        ]
    },
    output: {
         path: path.resolve(__dirname, 'dist'),
         filename: '[name].[chunkhash].js'
    },
    plugins: [
        new BundleTracker({ filename: './webpack-stats.json' }),
        new StyleLintPlugin({
            context: './src/styles/'
        }),
        new ExtractTextPlugin({ filename: '[name].[contenthash].css' }),
        new webpack.ProvidePlugin({
            $: 'jquery',
            jQuery: 'jquery',
            'window.jQuery': 'jquery',
            Popper: ['popper.js', 'default'],
        }),
        new CleanWebpackPlugin(['dist'], {
          root: path.resolve(),
          verbose: true,
          dry: false
        })
    ],
    resolve: {
        modules: [
            'node_modules',
            path.join(__dirname, "src")
        ],
        extensions: ['.js', '.jsx'],
    }
}

if (release) {
    config.plugins.push(
        new webpack.DefinePlugin({
            'DEBUG': false,
            'PRODUCTION': true,
            'process.env.NODE_ENV': JSON.stringify('production')
        }),
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
        })
    );
} else {
    config.performance = {
        assetFilter: function(assetFilename) {
            return assetFilename.endsWith('.js') || assetFilename.endsWith('.css');
        },
        hints: "warning",
        maxEntrypointSize: 1000000
    };

    config.profile = true;

    config.plugins.push(
        new webpack.DefinePlugin({
            'DEBUG': true,
            'PRODUCTION': false
        })
    );
}

config.plugins.push(
    new webpack.optimize.CommonsChunkPlugin({
        name: 'vendor',
        minChunks: function (module) {
           return module.context && module.context.indexOf('node_modules') !== -1;
        }
    }),
    new webpack.optimize.CommonsChunkPlugin({
        name: "manifest",
        minChunks: Infinity
    })
);

module.exports = config;
