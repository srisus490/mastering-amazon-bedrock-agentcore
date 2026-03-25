# Configuration Directory

This directory contains configuration files for the File Monitoring System.

## Files

- **logging.yaml** - Logging configuration (if needed for advanced setups)
- **monitoring_dirs.yaml** - Directory monitoring configuration (example)

## Environment Variables

The application uses environment variables for configuration. See `.env.example` in the root directory for all available options.

## Configuration Priority

1. Environment variables (highest priority)
2. `.env` file
3. Default values in code (lowest priority)

## Adding New Configuration

When adding new configuration options:

1. Add the field to the appropriate config class in `src/core/config.py`
2. Add the default value
3. Document it in `.env.example`
4. Add tests in `tests/test_config.py`
