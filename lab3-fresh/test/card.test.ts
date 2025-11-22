/* Copyright (c) 2021-25 MIT 6.102/6.031 course staff, all rights reserved.
 * Redistribution of original or derived work requires permission of course staff.
 */

import assert from 'node:assert';
import { Card } from '../src/card.js';

/**
 * Tests for the Card class.
 */
describe('Card', function() {
    
    describe('constructor', function() {
        it('should create a card with initial values', function() {
            const card = new Card('A', false, false);
            assert.strictEqual(card.value, 'A');
            assert.strictEqual(card.faceUp, false);
            assert.strictEqual(card.isBusy, false);
        });

        it('should create a face-up card', function() {
            const card = new Card('B', true, false);
            assert.strictEqual(card.value, 'B');
            assert.strictEqual(card.faceUp, true);
            assert.strictEqual(card.isBusy, false);
        });

        it('should create a busy card', function() {
            const card = new Card('C', false, true);
            assert.strictEqual(card.value, 'C');
            assert.strictEqual(card.faceUp, false);
            assert.strictEqual(card.isBusy, true);
        });
    });

    describe('getValue', function() {
        it('should return value when face up', function() {
            const card = new Card('A', true, false);
            const value = card.getValue();
            assert.strictEqual(value, 'A');
        });

        it('should return undefined when face down', function() {
            const card = new Card('A', false, false);
            const value = card.getValue();
            assert.strictEqual(value, undefined);
        });

        it('should return undefined even if busy when face down', function() {
            const card = new Card('A', false, true);
            const value = card.getValue();
            assert.strictEqual(value, undefined);
        });
    });

    describe('getFaceUp', function() {
        it('should return true for face-up card', async function() {
            const card = new Card('A', true, false);
            const faceUp = await card.getFaceUp();
            assert.strictEqual(faceUp, true);
        });

        it('should return false for face-down card', async function() {
            const card = new Card('A', false, false);
            const faceUp = await card.getFaceUp();
            assert.strictEqual(faceUp, false);
        });
    });

    describe('getIsBusy', function() {
        it('should return true for busy card', async function() {
            const card = new Card('A', false, true);
            const isBusy = await card.getIsBusy();
            assert.strictEqual(isBusy, true);
        });

        it('should return false for non-busy card', async function() {
            const card = new Card('A', false, false);
            const isBusy = await card.getIsBusy();
            assert.strictEqual(isBusy, false);
        });
    });

    describe('setFaceUp', function() {
        it('should set card to face up', async function() {
            const card = new Card('A', false, false);
            await card.setFaceUp(true);
            assert.strictEqual(card.faceUp, true);
            const faceUp = await card.getFaceUp();
            assert.strictEqual(faceUp, true);
        });

        it('should set card to face down', async function() {
            const card = new Card('A', true, false);
            await card.setFaceUp(false);
            assert.strictEqual(card.faceUp, false);
            const faceUp = await card.getFaceUp();
            assert.strictEqual(faceUp, false);
        });

        it('should return the card instance', async function() {
            const card = new Card('A', false, false);
            const result = await card.setFaceUp(true);
            assert.strictEqual(result, card);
        });
    });

    describe('setIsBusy', function() {
        it('should set card to busy', async function() {
            const card = new Card('A', false, false);
            await card.setIsBusy(true);
            assert.strictEqual(card.isBusy, true);
            const isBusy = await card.getIsBusy();
            assert.strictEqual(isBusy, true);
        });

        it('should set card to not busy', async function() {
            const card = new Card('A', false, true);
            await card.setIsBusy(false);
            assert.strictEqual(card.isBusy, false);
            const isBusy = await card.getIsBusy();
            assert.strictEqual(isBusy, false);
        });

        it('should return the card instance', async function() {
            const card = new Card('A', false, false);
            const result = await card.setIsBusy(true);
            assert.strictEqual(result, card);
        });
    });

    describe('setValue', function() {
        it('should change card value', async function() {
            const card = new Card('A', false, false);
            await card.setValue('B');
            assert.strictEqual(card.value, 'B');
        });

        it('should change value even when face down', async function() {
            const card = new Card('A', false, false);
            await card.setValue('C');
            assert.strictEqual(card.value, 'C');
            // Value should change but getValue still returns undefined when face down
            const value = card.getValue();
            assert.strictEqual(value, undefined);
        });

        it('should change value and be visible when face up', async function() {
            const card = new Card('A', true, false);
            await card.setValue('D');
            assert.strictEqual(card.value, 'D');
            const value = card.getValue();
            assert.strictEqual(value, 'D');
        });

        it('should return the card instance', async function() {
            const card = new Card('A', false, false);
            const result = await card.setValue('B');
            assert.strictEqual(result, card);
        });
    });

    describe('combined operations', function() {
        it('should handle multiple state changes', async function() {
            const card = new Card('A', false, false);
            await card.setFaceUp(true);
            await card.setIsBusy(true);
            await card.setValue('B');
            
            assert.strictEqual(card.value, 'B');
            assert.strictEqual(card.faceUp, true);
            assert.strictEqual(card.isBusy, true);
            const value = card.getValue();
            assert.strictEqual(value, 'B');
        });

        it('should maintain state consistency', async function() {
            const card = new Card('X', true, true);
            const value1 = card.getValue();
            await card.setFaceUp(false);
            const value2 = card.getValue();
            await card.setFaceUp(true);
            await card.setValue('Y');
            const value3 = card.getValue();
            
            assert.strictEqual(value1, 'X');
            assert.strictEqual(value2, undefined);
            assert.strictEqual(value3, 'Y');
        });
    });
});


