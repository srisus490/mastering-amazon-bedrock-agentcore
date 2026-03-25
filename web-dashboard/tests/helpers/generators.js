/**
 * Fast-check Generators
 * Custom generators for property-based testing
 */

import fc from 'fast-check';

/**
 * Generate a random source system
 */
export const systemGenerator = () => fc.record({
    sourceSystemId: fc.string({ minLength: 3, maxLength: 20 }),
    systemName: fc.string({ minLength: 5, maxLength: 50 }),
    status: fc.constantFrom('healthy', 'warning', 'critical'),
    fileCount: fc.nat({ max: 10000 }),
    lastFileArrival: fc.option(fc.date(), { nil: null }),
    slaScore: fc.integer({ min: 0, max: 100 }),
    hasViolations: fc.boolean()
});

/**
 * Generate a random file arrival
 */
export const fileArrivalGenerator = () => fc.record({
    id: fc.uuid(),
    sourceSystemId: fc.string({ minLength: 3, maxLength: 20 }),
    fileName: fc.string({ minLength: 5, maxLength: 100 }),
    arrivalTime: fc.date(),
    fileSize: fc.nat({ max: 1000000000 }),
    status: fc.constantFrom('processed', 'pending', 'failed'),
    processingTime: fc.option(fc.nat({ max: 60000 }), { nil: null })
});

/**
 * Generate a random SLA violation
 */
export const slaViolationGenerator = () => fc.record({
    id: fc.uuid(),
    sourceSystemId: fc.string({ minLength: 3, maxLength: 20 }),
    severity: fc.constantFrom('high', 'medium', 'low'),
    violationType: fc.string({ minLength: 5, maxLength: 50 }),
    timestamp: fc.date(),
    description: fc.string({ minLength: 10, maxLength: 200 }),
    resolved: fc.boolean()
});

/**
 * Generate random filter parameters
 */
export const filterGenerator = () => fc.record({
    sourceSystemId: fc.option(fc.string({ minLength: 3, maxLength: 20 }), { nil: null }),
    startDate: fc.option(fc.date(), { nil: null }),
    endDate: fc.option(fc.date(), { nil: null }),
    severity: fc.option(fc.constantFrom('high', 'medium', 'low'), { nil: null })
});
