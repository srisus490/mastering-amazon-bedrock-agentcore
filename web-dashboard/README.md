# File Monitoring Dashboard

A web-based dashboard for monitoring and visualizing the Intelligent File Monitoring System. Built with vanilla JavaScript, HTML5, and CSS3 for simplicity and ease of deployment.

## Features

- **Real-time Monitoring**: Auto-refresh every 30 seconds to display current system status
- **System Overview**: View all monitored source systems at a glance
- **File Arrival Statistics**: Track file arrivals with detailed timestamps and status
- **SLA Compliance**: Monitor SLA scores and violations with severity indicators
- **Trend Visualization**: Interactive charts showing daily trends, moving averages, and hourly patterns
- **Filtering**: Filter data by source system, date range, and severity
- **Error Handling**: Graceful error handling with retry logic and offline detection

## Prerequisites

### For Running the Dashboard

- A modern web browser (Chrome 90+, Firefox 88+, Safari 14+, or Edge 90+)
- A simple HTTP server (any of the following):
  - Python 3: `python -m http.server`
  - Node.js: `npx serve`
  - PHP: `php -S localhost:8000`
- The FastAPI backend running at `http://localhost:8000` (or configured URL)

### For Development and Testing

- Node.js 18+ (for running tests)
- npm or yarn

## Quick Start

### 1. Clone or Download

```bash
# If part of a larger repository
cd web-dashboard

# Or download the web-dashboard folder directly
```

### 2. Configure API URL

Edit `config/config.json` to set your backend API URL:

```json
{
  "apiBaseURL": "http://localhost:8000",
  "refreshInterval": 30000,
  "cacheTimeout": 30000,
  "retryAttempts": 3,
  "retryBackoff": 100,
  "chartMaxDataPoints": 100,
  "paginationPageSize": 50
}
```

**Configuration Options:**
- `apiBaseURL`: Backend API base URL (default: `http://localhost:8000`)
- `refreshInterval`: Auto-refresh interval in milliseconds (default: 30000 = 30 seconds)
- `cacheTimeout`: API response cache duration in milliseconds (default: 30000)
- `retryAttempts`: Number of retry attempts for failed API calls (default: 3)
- `retryBackoff`: Initial backoff delay for retries in milliseconds (default: 100)
- `chartMaxDataPoints`: Maximum data points to display in charts (default: 100)
- `paginationPageSize`: Number of items per page in file arrival lists (default: 50)

### 3. Start a Local Server

Choose one of the following methods:

**Using Python:**
```bash
python -m http.server 8080
```

**Using Node.js (npx serve):**
```bash
npx serve . -p 8080
```

**Using PHP:**
```bash
php -S localhost:8080
```

**Using npm (if you installed dependencies):**
```bash
npm run serve
```

### 4. Open in Browser

Navigate to `http://localhost:8080` in your web browser.

## Development

### Install Dependencies

```bash
npm install
```

### Run Tests

```bash
# Run all tests
npm test

# Run only unit tests
npm run test:unit

# Run only property-based tests
npm run test:property

# Run tests in watch mode
npm run test:watch

# Generate coverage report
npm run coverage
```

### Project Structure

```
web-dashboard/
├── index.html              # Main HTML file
├── css/                    # Stylesheets
│   ├── main.css           # Main styles
│   ├── components.css     # Component-specific styles
│   └── responsive.css     # Responsive design styles
├── js/                     # JavaScript modules
│   ├── app.js             # Main application orchestration
│   ├── api-client.js      # API communication layer
│   ├── state-manager.js   # State management
│   ├── ui-manager.js      # UI rendering and updates
│   ├── chart-renderer.js  # Chart.js wrapper
│   └── utils.js           # Utility functions
├── config/                 # Configuration files
│   └── config.json        # Application configuration
├── tests/                  # Test files
│   ├── unit/              # Unit tests
│   ├── property/          # Property-based tests
│   ├── integration/       # Integration tests
│   └── helpers/           # Test helpers and fixtures
├── package.json           # Node.js dependencies and scripts
└── README.md              # This file
```

## Deployment

### Local Deployment

Follow the Quick Start instructions above. The dashboard is a static web application and can be served by any HTTP server.

### AWS S3 + CloudFront Deployment

1. **Create S3 Bucket:**
```bash
aws s3 mb s3://your-dashboard-bucket
```

2. **Configure Bucket for Static Website Hosting:**
```bash
aws s3 website s3://your-dashboard-bucket --index-document index.html
```

3. **Upload Files:**
```bash
aws s3 sync . s3://your-dashboard-bucket --exclude "node_modules/*" --exclude "tests/*" --exclude ".git/*"
```

4. **Set Bucket Policy for Public Access:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::your-dashboard-bucket/*"
    }
  ]
}
```

5. **Create CloudFront Distribution** (optional, for HTTPS and CDN):
   - Origin: Your S3 bucket website endpoint
   - Default Root Object: `index.html`
   - Enable HTTPS

6. **Update Configuration:**
   - Update `config/config.json` with your production API URL
   - Ensure CORS is configured on your backend API

### Other Hosting Options

- **Netlify**: Drag and drop the `web-dashboard` folder
- **Vercel**: Deploy with `vercel deploy`
- **GitHub Pages**: Push to a repository and enable GitHub Pages
- **Any Web Server**: Copy files to your web server's document root

## Usage

### Viewing System Overview

The dashboard loads with an overview of all monitored source systems. Each system card shows:
- System name
- Current status (healthy, warning, critical)
- Latest file count
- SLA score
- Warning indicators for violations

### Selecting a System

Click on a system card or use the dropdown filter to view detailed information for a specific system:
- File arrival history with timestamps
- SLA compliance metrics and violations
- Trend charts (daily, moving average, hourly patterns)

### Applying Filters

Use the filter controls at the top to narrow down data:
- **Source System**: Select a specific system
- **Date Range**: Set start and end dates
- **Severity**: Filter SLA violations by severity (high, medium, low)
- **Clear Filters**: Reset all filters to defaults

### Manual Refresh

Click the "Refresh" button in the header to immediately update all data. The dashboard also auto-refreshes every 30 seconds.

### Interpreting Status Colors

- **Green**: Healthy, no issues
- **Yellow**: Warning, minor issues or approaching thresholds
- **Red**: Critical, SLA violations or system errors
- **Orange**: Medium severity violations
- **Blue**: Low severity violations

## Troubleshooting

### Dashboard Shows "Network connectivity lost"

**Cause**: The browser cannot reach the backend API.

**Solutions:**
1. Verify the backend API is running: `curl http://localhost:8000/api/v1/health`
2. Check the API URL in `config/config.json`
3. Ensure no firewall is blocking the connection
4. Check browser console for detailed error messages

### Dashboard Shows "Error loading data"

**Cause**: API returned an error or invalid data.

**Solutions:**
1. Check the backend API logs for errors
2. Verify the API endpoints are responding correctly
3. Check browser console for detailed error messages
4. Try the manual refresh button

### Charts Not Displaying

**Cause**: Chart.js library failed to load or data format is incorrect.

**Solutions:**
1. Check browser console for JavaScript errors
2. Verify internet connection (Chart.js loads from CDN)
3. Check that trend data is available from the API
4. Try refreshing the page

### Filters Not Working

**Cause**: State management or API parameter issues.

**Solutions:**
1. Click "Clear Filters" and try again
2. Check browser console for errors
3. Verify date range is valid (start date before end date)
4. Refresh the page

### Performance Issues

**Cause**: Large datasets or slow API responses.

**Solutions:**
1. Use date range filters to limit data
2. Check backend API performance
3. Clear browser cache
4. Reduce `chartMaxDataPoints` in config.json

## Browser Compatibility

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

The dashboard uses modern JavaScript (ES6+) and may not work in older browsers.

## API Requirements

The dashboard expects the following API endpoints to be available:

- `GET /api/v1/trends/summary` - System overview
- `GET /api/v1/file-arrivals` - File arrival list
- `GET /api/v1/file-arrivals/count` - File count
- `GET /api/v1/sla/scores/{source_system_id}` - SLA scores
- `GET /api/v1/sla/average-score/{source_system_id}` - Average SLA score
- `GET /api/v1/sla/violations/by-severity/{source_system_id}` - SLA violations
- `GET /api/v1/trends/daily/{source_system_id}` - Daily trends
- `GET /api/v1/trends/moving-average/{source_system_id}` - Moving average
- `GET /api/v1/trends/hourly-patterns/{source_system_id}` - Hourly patterns

Ensure your backend API implements these endpoints and returns data in the expected format.

## Security Considerations

- The dashboard does not store sensitive data in localStorage
- All API calls use relative URLs to prevent CORS issues
- Input sanitization is applied to all user inputs
- For production deployment, use HTTPS and configure CSP headers

## Support

For issues, questions, or contributions, please refer to the main project repository or contact the development team.

## License

MIT License - See LICENSE file for details
