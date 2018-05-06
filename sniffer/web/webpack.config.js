const path = require('path');
const webpack = require('webpack');

const bundlePath = path.resolve(__dirname, '/lib/');

module.exports = {
  entry: './src/app.jsx',
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /(node_modules|bower_components)/,
        loader: 'babel-loader',
        options: { presets: ['env', 'react'] },
      },
    ],
  },
  resolve: { extensions: ['*', '.js', '.jsx'] },
  output: {
    publicPath: bundlePath,
    filename: 'app.js',
  },
  plugins: [new webpack.HotModuleReplacementPlugin()],
};
