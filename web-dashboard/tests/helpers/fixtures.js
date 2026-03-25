/**
 * Test Fixtures
 * Static test data for unit tests
 */

export const mockSystem = {
    sourceSystemId: 'TEST001',
    systemName: 'Test System',
    status: 'healthy',
    fileCount: 150,
    lastFileArrival: new Date('2024-01-15T10:30:00Z'),
    slaScore: 95,
    hasViolations: false
};

export const mockFileArrival = {
    id: '123e4567-e89b-12d3-a456-426614174000',
    sourceSystemId: 'TEST001',
    fileName: 'test_file.csv',
    arrivalTime: new Date('2024-01-15T10:30:00Z'),
    fileSize: 1024000,
    status: 'processed',
    processingTime: 5000
};

export const mockSLAViolation = {
    id: '123e4567-e89b-12d3-a456-426614174001',
    sourceSystemId: 'TEST001',
    severity: 'high',
    violationType: 'Late Arrival',
    timestamp: new Date('2024-01-15T10:30:00Z'),
    description: 'File arrived 2 hours late',
    resolved: false
};
