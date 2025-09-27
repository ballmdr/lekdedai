const path = require("path")
const BundleTracker = require("webpack-bundle-tracker")

module.exports = {
  entry: "./src/index.js",
  output: {
    path: path.resolve(__dirname, "dist/bundles"),
    filename: "[name]-[hash].js",
    publicPath: "/static/bundles/",
  },
  module: {
    rules: [
      {
        test: /\.jsx?$/,
        exclude: /node_modules/,
        use: {
          loader: "babel-loader",
          options: {
            presets: ["@babel/preset-react"],
          },
        },
      },
    ],
  },
  plugins: [new BundleTracker({ filename: "./webpack-stats.json" })],
}
