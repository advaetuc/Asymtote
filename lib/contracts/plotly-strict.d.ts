declare module "plotly.js/dist/plotly-strict.min.js" {
  import type * as Plotly from "plotly.js";
  const strictPlotly: typeof Plotly;
  export default strictPlotly;
}
