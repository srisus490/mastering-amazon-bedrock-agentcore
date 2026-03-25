# Knowledge Base Documents

This folder contains documentation for the Amazon Bedrock Knowledge Base used by the File Monitoring AI Assistant.

## Structure

```
kb-documents/
├── schema/          # Database schema documentation
├── systems/         # System descriptions and catalog
├── examples/        # Common query examples
├── sla/            # SLA definitions and calculations
└── troubleshooting/ # Common issues and solutions
```

## Usage

1. **Edit documents** in this folder as needed
2. **Upload to S3** bucket: `s3://file-monitoring-kb-docs-<your-account-id>/`
3. **Sync Knowledge Base** in AWS Bedrock Console
4. **Test** - Changes take effect in 5-10 minutes

## Updating Documents

### Add New Document
1. Create markdown file in appropriate folder
2. Upload to S3 in same folder structure
3. Sync Knowledge Base

### Update Existing Document
1. Edit markdown file
2. Re-upload to S3 (overwrites old version)
3. Sync Knowledge Base

### Delete Document
1. Delete from S3
2. Sync Knowledge Base

## Best Practices

- Use clear, concise language
- Include examples for complex concepts
- Keep documents focused on single topics
- Update regularly based on user questions
- Test retrieval after major changes

## S3 Upload Command

```bash
aws s3 sync . s3://file-monitoring-kb-docs-<your-account-id>/ --exclude "README.md"
```

## Last Updated
2026-02-19
