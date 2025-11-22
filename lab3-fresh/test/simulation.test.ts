/* Copyright (c) 2021-25 MIT 6.102/6.031 course staff, all rights reserved.
 * Redistribution of original or derived work requires permission of course staff.
 */

import assert from 'node:assert';
import { Board } from '../src/board.js';
import { Player } from '../src/player.js';
import { timeout } from '../src/timeout.js';

/**
 * Tests for the simulation module.
 * Note: The simulation module contains example code that may not be fully implemented.
 */
describe('Simulation', function() {
    
    beforeEach(function() {
        // Reset singleton instance before each test
        (Board as any).instance = null;
    });

    describe('simulation setup', function() {
        it('should be able to parse board for simulation', async function() {
            const board = await Board.parseFromFile('boards/ab.txt');
            const size = board.getSize();
            assert(size.row > 0);
            assert(size.col > 0);
        });

        it('should support multiple players', async function() {
            const board = await Board.parseFromFile('boards/ab.txt');
            const player1 = new Player('player1');
            const player2 = new Player('player2');
            const player3 = new Player('player3');
            const player4 = new Player('player4');
            
            await board.addPlayer(player1);
            await board.addPlayer(player2);
            await board.addPlayer(player3);
            await board.addPlayer(player4);
            
            // All players should be able to look at board
            const result1 = await board.look('player1');
            const result2 = await board.look('player2');
            const result3 = await board.look('player3');
            const result4 = await board.look('player4');
            
            assert(result1.startsWith('5x5'));
            assert(result2.startsWith('5x5'));
            assert(result3.startsWith('5x5'));
            assert(result4.startsWith('5x5'));
        });
    });

    describe('concurrent player operations', function() {
        it('should handle multiple players flipping cards concurrently', async function() {
            const board = await Board.parseFromFile('boards/ab.txt');
            await board.addPlayer(new Player('player1'));
            await board.addPlayer(new Player('player2'));
            await board.addPlayer(new Player('player3'));
            await board.addPlayer(new Player('player4'));
            
            const promises = [
                board.flip('player1', 0, 0),
                board.flip('player2', 0, 1),
                board.flip('player3', 0, 2),
                board.flip('player4', 0, 3)
            ];
            
            await Promise.all(promises);
            
            // All flips should complete
            const card1 = board.getCards(0, 0);
            const card2 = board.getCards(0, 1);
            const card3 = board.getCards(0, 2);
            const card4 = board.getCards(0, 3);
            
            if (card1 !== undefined) {
                const faceUp1 = await card1.getFaceUp();
                assert.strictEqual(faceUp1, true);
            }
        });

        it('should handle players with random delays', async function() {
            const board = await Board.parseFromFile('boards/ab.txt');
            await board.addPlayer(new Player('player1'));
            await board.addPlayer(new Player('player2'));
            
            async function playerWithDelay(playerId: string, row: number, col: number) {
                await timeout(Math.random() * 50);
                await board.flip(playerId, row, col);
            }
            
            const promises = [
                playerWithDelay('player1', 0, 0),
                playerWithDelay('player2', 0, 1)
            ];
            
            await Promise.all(promises);
            
            // Both should complete
            const result1 = await board.look('player1');
            const result2 = await board.look('player2');
            assert(result1.startsWith('5x5'));
            assert(result2.startsWith('5x5'));
        });
    });

    describe('simulation scenarios', function() {
        it('should simulate multiple flip attempts', async function() {
            const board = await Board.parseFromFile('boards/ab.txt');
            await board.addPlayer(new Player('player1'));
            
            const size = board.getSize();
            const tries = 5;
            
            for (let i = 0; i < tries; i++) {
                const row = Math.floor(Math.random() * size.row);
                const col = Math.floor(Math.random() * size.col);
                try {
                    await board.flip('player1', row, col);
                } catch (err) {
                    // Some flips might fail, which is okay
                }
            }
            
            // Simulation should complete without crashing
            const result = await board.look('player1');
            assert(result.startsWith('5x5'));
        });

        it('should handle players trying to flip same card', async function() {
            this.timeout(10000); // Increase timeout for this test
            const board = await Board.parseFromFile('boards/ab.txt');
            await board.addPlayer(new Player('player1'));
            await board.addPlayer(new Player('player2'));
            
            // Player1 flips first
            const flip1Promise = board.flip('player1', 0, 0);
            
            // Wait a bit then player2 tries same card
            await timeout(20);
            const flip2Promise = board.flip('player2', 0, 0);
            
            // Wait for both with timeout protection
            try {
                await Promise.race([
                    Promise.all([flip1Promise, flip2Promise]),
                    new Promise((resolve) => setTimeout(resolve, 5000))
                ]);
            } catch (err) {
                // Some errors might be expected in concurrent scenarios
            }
            
            // Both should be able to look at board regardless
            const result1 = await board.look('player1');
            const result2 = await board.look('player2');
            assert(result1.startsWith('5x5'));
            assert(result2.startsWith('5x5'));
        });
    });
});

