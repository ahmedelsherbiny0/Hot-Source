declare module "leaflet" {
  const L: any;
  export default L;
}

declare module "react-plotly.js" {
  import * as React from "react";
  const Plot: React.ComponentType<any>;
  export default Plot;
}
