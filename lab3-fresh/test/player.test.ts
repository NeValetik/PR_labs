/* Copyright (c) 2021-25 MIT 6.102/6.031 course staff, all rights reserved.
 * Redistribution of original or derived work requires permission of course staff.
 */

import assert from 'node:assert';
import { Player } from '../src/player.js';

/**
 * Tests for the Player class.
 */
describe('Player', function() {
    
    describe('constructor', function() {
        it('should create a player with an id', function() {
            const player = new Player('player1');
            assert.strictEqual(player.id, 'player1');
        });

        it('should create players with different ids', function() {
            const player1 = new Player('player1');
            const player2 = new Player('player2');
            assert.strictEqual(player1.id, 'player1');
            assert.strictEqual(player2.id, 'player2');
        });

        it('should allow empty string id', function() {
            const player = new Player('');
            assert.strictEqual(player.id, '');
        });

        it('should allow numeric string id', function() {
            const player = new Player('123');
            assert.strictEqual(player.id, '123');
        });

        it('should allow underscore in id', function() {
            const player = new Player('player_1');
            assert.strictEqual(player.id, 'player_1');
        });
    });

    describe('getId', function() {
        it('should return the player id', function() {
            const player = new Player('testplayer');
            const id = player.getId();
            assert.strictEqual(id, 'testplayer');
        });

        it('should return the same id as stored', function() {
            const id = 'my_player_id';
            const player = new Player(id);
            assert.strictEqual(player.getId(), id);
            assert.strictEqual(player.getId(), player.id);
        });

        it('should return empty string for empty id', function() {
            const player = new Player('');
            assert.strictEqual(player.getId(), '');
        });
    });
});


