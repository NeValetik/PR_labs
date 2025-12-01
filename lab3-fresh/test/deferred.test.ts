/* Copyright (c) 2021-25 MIT 6.102/6.031 course staff, all rights reserved.
 * Redistribution of original or derived work requires permission of course staff.
 */

import assert from 'node:assert';
import { Deferred } from '../src/deferred.js';

/**
 * Tests for the Deferred class.
 */
describe('Deferred', function() {
    
    describe('constructor', function() {
        it('should create a deferred with promise, resolve, and reject', function() {
            const deferred = new Deferred<string>();
            assert(deferred.promise instanceof Promise);
            assert(typeof deferred.resolve === 'function');
            assert(typeof deferred.reject === 'function');
        });
    });

    describe('resolve', function() {
        it('should resolve the promise with a value', async function() {
            const deferred = new Deferred<string>();
            deferred.resolve('test value');
            const value = await deferred.promise;
            assert.strictEqual(value, 'test value');
        });

        it('should resolve with different types', async function() {
            const deferred1 = new Deferred<number>();
            deferred1.resolve(42);
            const value1 = await deferred1.promise;
            assert.strictEqual(value1, 42);

            const deferred2 = new Deferred<boolean>();
            deferred2.resolve(true);
            const value2 = await deferred2.promise;
            assert.strictEqual(value2, true);
        });

        it('should resolve with undefined', async function() {
            const deferred = new Deferred<void>();
            deferred.resolve(undefined);
            await deferred.promise;
            // Should not throw
        });

        it('should resolve with object', async function() {
            const deferred = new Deferred<{ name: string }>();
            const obj = { name: 'test' };
            deferred.resolve(obj);
            const value = await deferred.promise;
            assert.deepStrictEqual(value, obj);
        });
    });

    describe('reject', function() {
        it('should reject the promise with an error', async function() {
            const deferred = new Deferred<string>();
            const error = new Error('test error');
            deferred.reject(error);
            
            await assert.rejects(
                async () => await deferred.promise,
                Error,
                'test error'
            );
        });

        it('should reject with different error messages', async function() {
            const deferred = new Deferred<string>();
            const error = new Error('different error');
            deferred.reject(error);
            
            await assert.rejects(
                async () => await deferred.promise,
                Error,
                'different error'
            );
        });
    });

    describe('promise behavior', function() {
        it('should allow multiple awaiters', async function() {
            const deferred = new Deferred<string>();
            const promise1 = deferred.promise;
            const promise2 = deferred.promise;
            
            deferred.resolve('shared value');
            
            const value1 = await promise1;
            const value2 = await promise2;
            
            assert.strictEqual(value1, 'shared value');
            assert.strictEqual(value2, 'shared value');
        });

        it('should handle resolve after await', async function() {
            const deferred = new Deferred<string>();
            const promise = deferred.promise;
            
            setTimeout(() => {
                deferred.resolve('delayed value');
            }, 10);
            
            const value = await promise;
            assert.strictEqual(value, 'delayed value');
        });

        it('should handle reject after await', async function() {
            const deferred = new Deferred<string>();
            const promise = deferred.promise;
            
            setTimeout(() => {
                deferred.reject(new Error('delayed error'));
            }, 10);
            
            await assert.rejects(
                async () => await promise,
                Error,
                'delayed error'
            );
        });
    });

    describe('multiple resolves/rejects', function() {
        it('should ignore subsequent resolves', async function() {
            const deferred = new Deferred<string>();
            deferred.resolve('first');
            deferred.resolve('second');
            
            const value = await deferred.promise;
            assert.strictEqual(value, 'first');
        });

        it('should ignore subsequent rejects after resolve', async function() {
            const deferred = new Deferred<string>();
            deferred.resolve('resolved');
            deferred.reject(new Error('rejected'));
            
            const value = await deferred.promise;
            assert.strictEqual(value, 'resolved');
        });
    });
});



