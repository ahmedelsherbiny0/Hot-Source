declare module "plotly.js-basic-dist" {
  const Plotly: any;
  export default Plotly;
}

declare module "react-plotly.js/factory" {
  const createPlotlyComponent: (plotly: any) => any;
  export default createPlotlyComponent;
}
