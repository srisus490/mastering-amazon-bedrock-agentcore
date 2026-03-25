/**
 * Chart Renderer Module
 * Chart.js wrapper for creating and updating visualizations
 */

export class ChartRenderer {
    constructor() {
        this.charts = new Map(); // Store chart instances by canvas ID
        this.maxDataPoints = 100; // Requirement 9.4: Limit to 100 points
    }

    /**
     * Get default chart options with tooltips and responsive settings
     */
    getDefaultChartOptions() {
        return {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                tooltip: {
                    enabled: true,
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        title: (context) => {
                            return context[0].label || '';
                        },
                        label: (context) => {
                            const label = context.dataset.label || '';
                            const value = context.parsed.y;
                            return `${label}: ${value}`;
                        }
                    }
                },
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        };
    }

    /**
     * Get color scheme for charts
     */
    getChartColors() {
        return {
            primary: 'rgba(54, 162, 235, 1)',
            primaryLight: 'rgba(54, 162, 235, 0.2)',
            success: 'rgba(75, 192, 192, 1)',
            successLight: 'rgba(75, 192, 192, 0.2)',
            warning: 'rgba(255, 206, 86, 1)',
            warningLight: 'rgba(255, 206, 86, 0.2)',
            danger: 'rgba(255, 99, 132, 1)',
            dangerLight: 'rgba(255, 99, 132, 0.2)',
            info: 'rgba(153, 102, 255, 1)',
            infoLight: 'rgba(153, 102, 255, 0.2)'
        };
    }

    /**
     * Limit data points to max 100 for performance (Requirement 9.4)
     */
    limitDataPoints(data) {
        if (!data || !Array.isArray(data)) {
            return data;
        }

        if (data.length <= this.maxDataPoints) {
            return data;
        }

        // Sample data evenly to get exactly maxDataPoints
        const step = data.length / this.maxDataPoints;
        const sampled = [];
        for (let i = 0; i < this.maxDataPoints; i++) {
            const index = Math.floor(i * step);
            sampled.push(data[index]);
        }
        return sampled;
    }

    /**
     * Create daily trend chart (line chart)
     * Requirement 4.1: Display line chart of daily file counts
     */
    createDailyTrendChart(canvasId, data) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            console.error(`Canvas element ${canvasId} not found`);
            return null;
        }

        // Destroy existing chart if present
        this.destroyChart(canvasId);

        // Limit data points
        const limitedData = this.limitDataPoints(data.dataPoints || []);

        const colors = this.getChartColors();
        const chartData = {
            labels: limitedData.map(point => {
                const date = new Date(point.timestamp);
                return date.toLocaleDateString();
            }),
            datasets: [{
                label: 'Daily File Count',
                data: limitedData.map(point => point.value),
                borderColor: colors.primary,
                backgroundColor: colors.primaryLight,
                tension: 0.1,
                fill: true
            }]
        };

        const options = {
            ...this.getDefaultChartOptions(),
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'File Count'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                }
            }
        };

        const chart = new Chart(canvas, {
            type: 'line',
            data: chartData,
            options: options
        });

        this.charts.set(canvasId, chart);
        return chart;
    }

    /**
     * Create moving average chart (line chart with smooth curve)
     * Requirement 4.1: Display moving average trends
     */
    createMovingAverageChart(canvasId, data) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            console.error(`Canvas element ${canvasId} not found`);
            return null;
        }

        this.destroyChart(canvasId);

        const limitedData = this.limitDataPoints(data.dataPoints || []);

        const colors = this.getChartColors();
        const chartData = {
            labels: limitedData.map(point => {
                const date = new Date(point.timestamp);
                return date.toLocaleDateString();
            }),
            datasets: [{
                label: 'Moving Average',
                data: limitedData.map(point => point.value),
                borderColor: colors.success,
                backgroundColor: colors.successLight,
                tension: 0.4, // Smoother curve for moving average
                fill: true
            }]
        };

        const options = {
            ...this.getDefaultChartOptions(),
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Average File Count'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                }
            }
        };

        const chart = new Chart(canvas, {
            type: 'line',
            data: chartData,
            options: options
        });

        this.charts.set(canvasId, chart);
        return chart;
    }

    /**
     * Create hourly pattern chart (bar chart)
     * Requirement 4.1: Display hourly patterns
     */
    createHourlyPatternChart(canvasId, data) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            console.error(`Canvas element ${canvasId} not found`);
            return null;
        }

        this.destroyChart(canvasId);

        const limitedData = this.limitDataPoints(data.dataPoints || []);

        const colors = this.getChartColors();
        const chartData = {
            labels: limitedData.map(point => {
                // Assuming timestamp represents hour (0-23)
                const date = new Date(point.timestamp);
                return `${date.getHours()}:00`;
            }),
            datasets: [{
                label: 'Files per Hour',
                data: limitedData.map(point => point.value),
                backgroundColor: colors.info,
                borderColor: colors.info,
                borderWidth: 1
            }]
        };

        const options = {
            ...this.getDefaultChartOptions(),
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'File Count'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Hour of Day'
                    }
                }
            }
        };

        const chart = new Chart(canvas, {
            type: 'bar',
            data: chartData,
            options: options
        });

        this.charts.set(canvasId, chart);
        return chart;
    }

    /**
     * Create SLA score chart (line chart with threshold line)
     * Requirement 3.7: Display SLA scores with warning threshold at 80
     */
    createSLAScoreChart(canvasId, data) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            console.error(`Canvas element ${canvasId} not found`);
            return null;
        }

        this.destroyChart(canvasId);

        const limitedData = this.limitDataPoints(data.dataPoints || []);

        const colors = this.getChartColors();
        const chartData = {
            labels: limitedData.map(point => {
                const date = new Date(point.timestamp);
                return date.toLocaleDateString();
            }),
            datasets: [
                {
                    label: 'SLA Score',
                    data: limitedData.map(point => point.value),
                    borderColor: colors.primary,
                    backgroundColor: colors.primaryLight,
                    tension: 0.1,
                    fill: false
                },
                {
                    label: 'Warning Threshold (80)',
                    data: limitedData.map(() => 80),
                    borderColor: colors.warning,
                    borderDash: [5, 5],
                    borderWidth: 2,
                    fill: false,
                    pointRadius: 0
                }
            ]
        };

        const options = {
            ...this.getDefaultChartOptions(),
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'SLA Score (%)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                }
            }
        };

        const chart = new Chart(canvas, {
            type: 'line',
            data: chartData,
            options: options
        });

        this.charts.set(canvasId, chart);
        return chart;
    }

    /**
     * Update existing chart with new data
     */
    updateChart(chartId, newData) {
        const chart = this.charts.get(chartId);
        if (!chart) {
            console.warn(`Chart ${chartId} not found for update`);
            return false;
        }

        const limitedData = this.limitDataPoints(newData.dataPoints || []);

        // Update labels
        chart.data.labels = limitedData.map(point => {
            const date = new Date(point.timestamp);
            return date.toLocaleDateString();
        });

        // Update dataset values
        if (chart.data.datasets[0]) {
            chart.data.datasets[0].data = limitedData.map(point => point.value);
        }

        chart.update();
        return true;
    }

    /**
     * Destroy chart and clean up resources
     */
    destroyChart(chartId) {
        const chart = this.charts.get(chartId);
        if (chart) {
            chart.destroy();
            this.charts.delete(chartId);
            return true;
        }
        return false;
    }

    /**
     * Destroy all charts
     */
    destroyAllCharts() {
        this.charts.forEach((chart, id) => {
            chart.destroy();
        });
        this.charts.clear();
    }
}
