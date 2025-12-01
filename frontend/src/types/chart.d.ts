// Type definitions for Chart.js v4
declare module 'chart.js' {
  interface ChartConfiguration<TType = any, Data = any> {
    type?: string;
    data?: Data;
    options?: ChartOptions<TType>;
  }

  interface ChartOptions<TType = any, Data = any> {
    responsive?: boolean;
    maintainAspectRatio?: boolean;
    plugins?: any[];
    animation?: false | {
      duration: number;
      easing: string;
      onProgress?: (this: Chart<TType>, type: 'update', args: any) => void;
      onComplete?: (this: Chart<TType>, type: 'update', args: any) => void;
    };
  }

  interface Chart<TType = any> {
    config?: ChartConfiguration<TType>;
    data?: Data;
  }

  // Chart constructors
  function chart<TType = any, Data = any>(
    ctx: CanvasRenderingContext2D,
    config?: ChartConfiguration<TType>
  ): Chart<TType>;
}

// Vue-ChartJS types
declare module 'vue-chartjs' {
  interface ChartComponent extends Chart {
    $props: Record<string, any>;
    $emit: (event: string, ...args: any[]) => void;
  }
}