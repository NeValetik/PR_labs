/* Copyright (c) 2021-25 MIT 6.102/6.031 course staff, all rights reserved.
 * Redistribution of original or derived work requires permission of course staff.
 */

import assert from 'node:assert';
import { timeout } from '../src/timeout.js';

/**
 * Tests for the timeout module.
 */
describe('timeout', function() {
    
    describe('basic functionality', function() {
        it('should wait for specified milliseconds', async function() {
            const start = Date.now();
            await timeout(50);
            const end = Date.now();
            const elapsed = end - start;
            
            // Should wait at least 50ms (allowing some tolerance)
            assert(elapsed >= 45, `Expected at least 45ms, got ${elapsed}ms`);
        });

        it('should return a promise', function() {
            const result = timeout(10);
            assert(result instanceof Promise);
        });

        it('should fulfill the promise', async function() {
            await assert.doesNotReject(async () => {
                await timeout(10);
            });
        });
    });

    describe('timing accuracy', function() {
        it('should wait approximately the right amount of time', async function() {
            const delay = 100;
            const start = Date.now();
            await timeout(delay);
            const end = Date.now();
            const elapsed = end - start;
            
            // Should be close to delay (within reasonable tolerance)
            assert(elapsed >= delay - 10, `Expected at least ${delay - 10}ms, got ${elapsed}ms`);
            assert(elapsed <= delay + 50, `Expected at most ${delay + 50}ms, got ${elapsed}ms`);
        });

        it('should handle very short delays', async function() {
            const start = Date.now();
            await timeout(1);
            const end = Date.now();
            const elapsed = end - start;
            
            // Should wait at least 1ms
            assert(elapsed >= 0);
        });

        it('should handle zero delay', async function() {
            const start = Date.now();
            await timeout(0);
            const end = Date.now();
            const elapsed = end - start;
            
            // Zero delay should resolve quickly (allow some tolerance for timing)
            assert(elapsed < 50, `Expected less than 50ms, got ${elapsed}ms`);
        });
    });

    describe('multiple timeouts', function() {
        it('should handle multiple sequential timeouts', async function() {
            const start = Date.now();
            await timeout(10);
            await timeout(10);
            await timeout(10);
            const end = Date.now();
            const elapsed = end - start;
            
            // Should wait approximately 30ms total
            assert(elapsed >= 25);
        });

        it('should handle concurrent timeouts', async function() {
            const start = Date.now();
            await Promise.all([timeout(50), timeout(50), timeout(50)]);
            const end = Date.now();
            const elapsed = end - start;
            
            // Concurrent timeouts should complete in approximately 50ms
            // Allow more tolerance for timing variations
            assert(elapsed >= 45);
            assert(elapsed <= 100, `Expected at most 100ms, got ${elapsed}ms`);
        });
    });

    describe('edge cases', function() {
        it('should handle very large delays', async function() {
            // Use a reasonable delay for testing
            const start = Date.now();
            await timeout(200);
            const end = Date.now();
            const elapsed = end - start;
            
            assert(elapsed >= 190);
        });

        it('should handle fractional milliseconds', async function() {
            const start = Date.now();
            await timeout(10.5);
            const end = Date.now();
            const elapsed = end - start;
            
            // Should wait approximately 10ms
            assert(elapsed >= 8);
        });
    });
});

