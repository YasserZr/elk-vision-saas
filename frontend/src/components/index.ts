// Components export
export * from './ui';
export * from './auth';
export * from './dashboard';

// Analytics exports (avoiding conflicts with dashboard)
export {
  TimeSeriesChart,
  MultiLineChart,
  BarChart,
  StackedBarChart,
  DoughnutChart,
  PieChartComponent,
  RealtimeChart,
  ChartCard,
  // Rename Sparkline to avoid conflict
  Sparkline as AnalyticsSparkline,
} from './analytics';
export type {
  TimeSeriesChartProps,
  MultiLineChartProps,
  BarChartProps,
  StackedBarChartProps,
  DoughnutChartProps,
  PieChartComponentProps,
  RealtimeChartProps,
  ChartCardProps,
  SparklineProps as AnalyticsSparklineProps,
} from './analytics';

export { SearchableTable } from './analytics';
export type {
  SearchableTableProps,
  Column as AnalyticsColumn,
} from './analytics';

export { KPICard, KPIGrid, KPIIcons } from './analytics';
export type { KPICardProps, KPIGridProps } from './analytics';

export { KibanaEmbed, KibanaVisualizationCard } from './analytics';
export type { KibanaEmbedProps, KibanaVisualizationCardProps } from './analytics';
