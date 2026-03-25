/**
 * Unit tests for Chart Renderer
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { ChartRenderer } from '../../js/chart-renderer.js';

// Mock Chart.js
global.Chart = vi.fn().mockImplementation((canvas, config) => {
    return {
        data: config.data,
        options: config.options,
        update: vi.fn(),
        destroy: vi.fn()
    };
});

describe('ChartRenderer', () => {
    let chartRenderer;

    beforeEach(() => {
        chartRenderer = new ChartRenderer();
        
        // Setup DOM with canvas elements
        document.body.innerHTML = `
            <canvas id="daily-trend-chart"></canvas>
            <canvas id="moving-average-chart"></canvas>
            <canvas id="hourly-pattern-chart"></canvas>
            <canvas id="sla-score-chart"></canvas>
        `;
    });

    afterEach(() => {
        chartRenderer.destroyAllCharts();
        vi.clearAllMocks();
    });

    describe('Constructor', () => {
        it('should initialize with empty charts map', () => {
            expect(chartRenderer.charts).toBeInstanceOf(Map);
            expect(chartRenderer.charts.size).toBe(0);
        });

        it('should set maxDataPoints to 100', () => {
            expect(chartRenderer.maxDataPoints).toBe(100);
        });
    });

    describe('getDefaultChartOptions', () => {
        it('should return options with responsive enabled', () => {
            const options = chartRenderer.getDefaultChartOptions();
            expect(options.responsive).toBe(true);
        });

        it('should return options with tooltip enabled', () => {
            const options = chartRenderer.getDefaultChartOptions();
            expect(options.plugins.tooltip.enabled).toBe(true);
        });

        it('should return options with legend displayed', () => {
            const options = chartRenderer.getDefaultChartOptions();
            expect(options.plugins.legend.display).toBe(true);
        });
    });

    describe('getChartColors', () => {
        it('should return color scheme with all required colors', () => {
            const colors = chartRenderer.getChartColors();
            expect(colors).toHaveProperty('primary');
            expect(colors).toHaveProperty('success');
            expect(colors).toHaveProperty('warning');
            expect(colors).toHaveProperty('danger');
            expect(colors).toHaveProperty('info');
        });

        it('should return colors with light variants', () => {
            const colors = chartRenderer.getChartColors();
            expect(colors).toHaveProperty('primaryLight');
            expect(colors).toHaveProperty('successLight');
        });
    });

    describe('limitDataPoints', () => {
        it('should return data unchanged when length <= 100', () => {
            const data = Array(50).fill(null).map((_, i) => ({ value: i }));
            const limited = chartRenderer.limitDataPoints(data);
            expect(limited.length).toBe(50);
        });

        it('should limit data to 100 points when length > 100', () => {
            const data = Array(200).fill(null).map((_, i) => ({ value: i }));
            const limited = chartRenderer.limitDataPoints(data);
            expect(limited.length).toBe(100);
        });

        it('should sample data evenly', () => {
            const data = Array(200).fill(null).map((_, i) => ({ value: i }));
            const limited = chartRenderer.limitDataPoints(data);
            
            // First and last elements should be preserved (approximately)
            expect(limited[0].value).toBe(0);
            expect(limited[limited.length - 1].value).toBeGreaterThan(150);
        });

        it('should handle null or undefined data', () => {
            expect(chartRenderer.limitDataPoints(null)).toBe(null);
            expect(chartRenderer.limitDataPoints(undefined)).toBe(undefined);
        });

        it('should handle non-array data', () => {
            const data = { value: 10 };
            expect(chartRenderer.limitDataPoints(data)).toBe(data);
        });
    });

    describe('createDailyTrendChart', () => {
        it('should create a line chart with correct data', () => {
            const data = {
                dataPoints: [
                    { timestamp: '2024-01-01', value: 10 },
                    { timestamp: '2024-01-02', value: 20 }
                ]
            };

            const chart = chartRenderer.createDailyTrendChart('daily-trend-chart', data);

            expect(Chart).toHaveBeenCalled();
            expect(chart).toBeDefined();
            expect(chartRenderer.charts.has('daily-trend-chart')).toBe(true);
        });

        it('should format dates as labels', () => {
            const data = {
                dataPoints: [
                    { timestamp: '2024-01-15T10:30:00', value: 10 }
                ]
            };

            chartRenderer.createDailyTrendChart('daily-trend-chart', data);

            const callArgs = Chart.mock.calls[0];
            const chartData = callArgs[1].data;
            expect(chartData.labels[0]).toContain('1/15/2024');
        });

        it('should limit data points to 100', () => {
            const data = {
                dataPoints: Array(200).fill(null).map((_, i) => ({
                    timestamp: `2024-01-${(i % 28) + 1}`,
                    value: i
                }))
            };

            chartRenderer.createDailyTrendChart('daily-trend-chart', data);

            const callArgs = Chart.mock.calls[0];
            const chartData = callArgs[1].data;
            expect(chartData.labels.length).toBe(100);
            expect(chartData.datasets[0].data.length).toBe(100);
        });

        it('should return null if canvas not found', () => {
            const data = { dataPoints: [] };
            const chart = chartRenderer.createDailyTrendChart('non-existent', data);
            expect(chart).toBe(null);
        });

        it('should destroy existing chart before creating new one', () => {
            const data = { dataPoints: [{ timestamp: '2024-01-01', value: 10 }] };
            
            const chart1 = chartRenderer.createDailyTrendChart('daily-trend-chart', data);
            const chart2 = chartRenderer.createDailyTrendChart('daily-trend-chart', data);

            expect(chart1.destroy).toHaveBeenCalled();
            expect(chartRenderer.charts.size).toBe(1);
        });
    });

    describe('createMovingAverageChart', () => {
        it('should create a line chart with smooth curve', () => {
            const data = {
                dataPoints: [
                    { timestamp: '2024-01-01', value: 10 },
                    { timestamp: '2024-01-02', value: 15 }
                ]
            };

            const chart = chartRenderer.createMovingAverageChart('moving-average-chart', data);

            expect(Chart).toHaveBeenCalled();
            expect(chart).toBeDefined();
            
            const callArgs = Chart.mock.calls[0];
            const chartData = callArgs[1].data;
            expect(chartData.datasets[0].tension).toBe(0.4);
        });

        it('should use success color scheme', () => {
            const data = {
                dataPoints: [{ timestamp: '2024-01-01', value: 10 }]
            };

            chartRenderer.createMovingAverageChart('moving-average-chart', data);

            const callArgs = Chart.mock.calls[0];
            const chartData = callArgs[1].data;
            const colors = chartRenderer.getChartColors();
            expect(chartData.datasets[0].borderColor).toBe(colors.success);
        });
    });

    describe('createHourlyPatternChart', () => {
        it('should create a bar chart', () => {
            const data = {
                dataPoints: [
                    { timestamp: '2024-01-01T10:00:00', value: 5 },
                    { timestamp: '2024-01-01T11:00:00', value: 8 }
                ]
            };

            const chart = chartRenderer.createHourlyPatternChart('hourly-pattern-chart', data);

            expect(Chart).toHaveBeenCalled();
            expect(chart).toBeDefined();
            
            const callArgs = Chart.mock.calls[0];
            expect(callArgs[1].type).toBe('bar');
        });

        it('should format hours as labels', () => {
            const data = {
                dataPoints: [
                    { timestamp: '2024-01-01T10:00:00', value: 5 },
                    { timestamp: '2024-01-01T14:00:00', value: 8 }
                ]
            };

            chartRenderer.createHourlyPatternChart('hourly-pattern-chart', data);

            const callArgs = Chart.mock.calls[0];
            const chartData = callArgs[1].data;
            expect(chartData.labels[0]).toBe('10:00');
            expect(chartData.labels[1]).toBe('14:00');
        });
    });

    describe('createSLAScoreChart', () => {
        it('should create a line chart with threshold line', () => {
            const data = {
                dataPoints: [
                    { timestamp: '2024-01-01', value: 95 },
                    { timestamp: '2024-01-02', value: 85 }
                ]
            };

            const chart = chartRenderer.createSLAScoreChart('sla-score-chart', data);

            expect(Chart).toHaveBeenCalled();
            expect(chart).toBeDefined();
            
            const callArgs = Chart.mock.calls[0];
            const chartData = callArgs[1].data;
            expect(chartData.datasets.length).toBe(2);
            expect(chartData.datasets[1].label).toContain('80');
        });

        it('should set threshold line at 80', () => {
            const data = {
                dataPoints: [
                    { timestamp: '2024-01-01', value: 95 },
                    { timestamp: '2024-01-02', value: 75 }
                ]
            };

            chartRenderer.createSLAScoreChart('sla-score-chart', data);

            const callArgs = Chart.mock.calls[0];
            const chartData = callArgs[1].data;
            expect(chartData.datasets[1].data[0]).toBe(80);
            expect(chartData.datasets[1].data[1]).toBe(80);
        });

        it('should use dashed line for threshold', () => {
            const data = {
                dataPoints: [{ timestamp: '2024-01-01', value: 95 }]
            };

            chartRenderer.createSLAScoreChart('sla-score-chart', data);

            const callArgs = Chart.mock.calls[0];
            const chartData = callArgs[1].data;
            expect(chartData.datasets[1].borderDash).toEqual([5, 5]);
        });

        it('should set y-axis max to 100', () => {
            const data = {
                dataPoints: [{ timestamp: '2024-01-01', value: 95 }]
            };

            chartRenderer.createSLAScoreChart('sla-score-chart', data);

            const callArgs = Chart.mock.calls[0];
            const options = callArgs[1].options;
            expect(options.scales.y.max).toBe(100);
        });
    });

    describe('updateChart', () => {
        it('should update existing chart with new data', () => {
            const initialData = {
                dataPoints: [{ timestamp: '2024-01-01', value: 10 }]
            };
            const newData = {
                dataPoints: [
                    { timestamp: '2024-01-02', value: 20 },
                    { timestamp: '2024-01-03', value: 30 }
                ]
            };

            chartRenderer.createDailyTrendChart('daily-trend-chart', initialData);
            const result = chartRenderer.updateChart('daily-trend-chart', newData);

            expect(result).toBe(true);
            const chart = chartRenderer.charts.get('daily-trend-chart');
            expect(chart.update).toHaveBeenCalled();
        });

        it('should return false if chart not found', () => {
            const newData = {
                dataPoints: [{ timestamp: '2024-01-01', value: 10 }]
            };

            const result = chartRenderer.updateChart('non-existent', newData);
            expect(result).toBe(false);
        });

        it('should limit data points when updating', () => {
            const initialData = {
                dataPoints: [{ timestamp: '2024-01-01', value: 10 }]
            };
            const newData = {
                dataPoints: Array(200).fill(null).map((_, i) => ({
                    timestamp: `2024-01-${(i % 28) + 1}`,
                    value: i
                }))
            };

            chartRenderer.createDailyTrendChart('daily-trend-chart', initialData);
            chartRenderer.updateChart('daily-trend-chart', newData);

            const chart = chartRenderer.charts.get('daily-trend-chart');
            expect(chart.data.labels.length).toBe(100);
        });
    });

    describe('destroyChart', () => {
        it('should destroy chart and remove from map', () => {
            const data = {
                dataPoints: [{ timestamp: '2024-01-01', value: 10 }]
            };

            chartRenderer.createDailyTrendChart('daily-trend-chart', data);
            const result = chartRenderer.destroyChart('daily-trend-chart');

            expect(result).toBe(true);
            expect(chartRenderer.charts.has('daily-trend-chart')).toBe(false);
        });

        it('should return false if chart not found', () => {
            const result = chartRenderer.destroyChart('non-existent');
            expect(result).toBe(false);
        });

        it('should call destroy method on chart instance', () => {
            const data = {
                dataPoints: [{ timestamp: '2024-01-01', value: 10 }]
            };

            const chart = chartRenderer.createDailyTrendChart('daily-trend-chart', data);
            chartRenderer.destroyChart('daily-trend-chart');

            expect(chart.destroy).toHaveBeenCalled();
        });
    });

    describe('destroyAllCharts', () => {
        it('should destroy all charts and clear map', () => {
            const data = {
                dataPoints: [{ timestamp: '2024-01-01', value: 10 }]
            };

            chartRenderer.createDailyTrendChart('daily-trend-chart', data);
            chartRenderer.createMovingAverageChart('moving-average-chart', data);
            chartRenderer.createHourlyPatternChart('hourly-pattern-chart', data);

            expect(chartRenderer.charts.size).toBe(3);

            chartRenderer.destroyAllCharts();

            expect(chartRenderer.charts.size).toBe(0);
        });

        it('should call destroy on all chart instances', () => {
            const data = {
                dataPoints: [{ timestamp: '2024-01-01', value: 10 }]
            };

            const chart1 = chartRenderer.createDailyTrendChart('daily-trend-chart', data);
            const chart2 = chartRenderer.createMovingAverageChart('moving-average-chart', data);

            chartRenderer.destroyAllCharts();

            expect(chart1.destroy).toHaveBeenCalled();
            expect(chart2.destroy).toHaveBeenCalled();
        });
    });

    describe('Chart Configuration', () => {
        it('should configure tooltips for all chart types', () => {
            const data = {
                dataPoints: [{ timestamp: '2024-01-01', value: 10 }]
            };

            chartRenderer.createDailyTrendChart('daily-trend-chart', data);

            const callArgs = Chart.mock.calls[0];
            const options = callArgs[1].options;
            expect(options.plugins.tooltip.enabled).toBe(true);
            expect(options.plugins.tooltip.callbacks).toBeDefined();
        });

        it('should make all charts responsive', () => {
            const data = {
                dataPoints: [{ timestamp: '2024-01-01', value: 10 }]
            };

            chartRenderer.createDailyTrendChart('daily-trend-chart', data);

            const callArgs = Chart.mock.calls[0];
            const options = callArgs[1].options;
            expect(options.responsive).toBe(true);
        });

        it('should configure y-axis to begin at zero', () => {
            const data = {
                dataPoints: [{ timestamp: '2024-01-01', value: 10 }]
            };

            chartRenderer.createDailyTrendChart('daily-trend-chart', data);

            const callArgs = Chart.mock.calls[0];
            const options = callArgs[1].options;
            expect(options.scales.y.beginAtZero).toBe(true);
        });
    });

    describe('Edge Cases', () => {
        it('should handle empty dataPoints array', () => {
            const data = { dataPoints: [] };
            const chart = chartRenderer.createDailyTrendChart('daily-trend-chart', data);
            
            expect(chart).toBeDefined();
            const callArgs = Chart.mock.calls[0];
            const chartData = callArgs[1].data;
            expect(chartData.labels.length).toBe(0);
        });

        it('should handle missing dataPoints property', () => {
            const data = {};
            const chart = chartRenderer.createDailyTrendChart('daily-trend-chart', data);
            
            expect(chart).toBeDefined();
        });

        it('should handle invalid timestamp formats gracefully', () => {
            const data = {
                dataPoints: [{ timestamp: 'invalid-date', value: 10 }]
            };

            const chart = chartRenderer.createDailyTrendChart('daily-trend-chart', data);
            expect(chart).toBeDefined();
        });
    });
});
