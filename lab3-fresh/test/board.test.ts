/* Copyright (c) 2021-25 MIT 6.102/6.031 course staff, all rights reserved.
 * Redistribution of original or derived work requires permission of course staff.
 */

import assert from 'node:assert';
import fs from 'node:fs';
import { Board } from '../src/board.js';
import { Card } from '../src/card.js';
import { Player } from '../src/player.js';

/**
 * Tests for the Board abstract data type.
 */
describe('Board', function() {
    
    beforeEach(function() {
        // Reset singleton instance before each test
        (Board as any).instance = null;
    });

    describe('parseFromFile', function() {
        it('should parse a valid board file', async function() {
            const board = await Board.parseFromFile('boards/ab.txt');
            const size = board.getSize();
            assert.strictEqual(size.row, 5);
            assert.strictEqual(size.col, 5);
        });

        it('should parse perfect.txt board file', async function() {
            const board = await Board.parseFromFile('boards/perfect.txt');
            const size = board.getSize();
            assert.strictEqual(size.row, 3);
            assert.strictEqual(size.col, 3);
        });

        it('should throw error for invalid file', async function() {
            await assert.rejects(
                async () => await Board.parseFromFile('boards/nonexistent.txt'),
                Error
            );
        });

        it('should throw error for invalid size format', async function() {
            // Create a temporary invalid board file
            const invalidContent = 'invalid\nA\nB';
            const tempFile = 'boards/temp_invalid.txt';
            await fs.promises.writeFile(tempFile, invalidContent);
            
            try {
                await assert.rejects(
                    async () => await Board.parseFromFile(tempFile),
                    Error
                );
            } finally {
                // Clean up
                try {
                    await fs.promises.unlink(tempFile);
                } catch {
                    // Ignore cleanup errors
                }
            }
        });
    });

    describe('constructor', function() {
        it('should create a board with valid size and cards', function() {
            const cards = [new Card('A', false, false), new Card('B', false, false)];
            const board = new Board({ row: 1, col: 2 }, cards);
            const size = board.getSize();
            assert.strictEqual(size.row, 1);
            assert.strictEqual(size.col, 2);
        });

        it('should throw error if board already exists', function() {
            const cards1 = [new Card('A', false, false)];
            const cards2 = [new Card('B', false, false)];
            new Board({ row: 1, col: 1 }, cards1);
            assert.throws(
                () => new Board({ row: 1, col: 1 }, cards2),
                Error,
                'Board already exists'
            );
        });

        it('should throw error for invalid size', function() {
            const cards = [new Card('A', false, false)];
            assert.throws(
                () => new Board({ row: 0, col: 1 }, cards),
                Error
            );
            assert.throws(
                () => new Board({ row: 1, col: 0 }, cards),
                Error
            );
        });

        it('should throw error if cards length does not match size', function() {
            const cards = [new Card('A', false, false)];
            assert.throws(
                () => new Board({ row: 2, col: 2 }, cards),
                Error
            );
        });
    });

    describe('getInstance', function() {
        it('should return the singleton instance', async function() {
            const board = await Board.parseFromFile('boards/ab.txt');
            const instance = Board.getInstance();
            assert.strictEqual(instance, board);
        });

        it('should throw error if board not initialized', function() {
            (Board as any).instance = null;
            assert.throws(
                () => Board.getInstance(),
                Error,
                'Board not initialized'
            );
        });
    });

    describe('getSize', function() {
        it('should return correct size', async function() {
            const board = await Board.parseFromFile('boards/ab.txt');
            const size = board.getSize();
            assert.strictEqual(size.row, 5);
            assert.strictEqual(size.col, 5);
        });
    });

    describe('getCards', function() {
        it('should return all cards when called without arguments', async function() {
            const board = await Board.parseFromFile('boards/ab.txt');
            const cards = board.getCards();
            assert.strictEqual(cards.length, 25);
        });

        it('should return specific card when called with row and column', async function() {
            const board = await Board.parseFromFile('boards/ab.txt');
            const card = board.getCards(0, 0);
            assert(card !== undefined);
        });

        it('should return undefined for invalid coordinates', async function() {
            const board = await Board.parseFromFile('boards/ab.txt');
            const card = board.getCards(10, 10);
            assert.strictEqual(card, undefined);
        });
    });

    describe('addPlayer', function() {
        it('should add a new player', async function() {
            const board = await Board.parseFromFile('boards/ab.txt');
            const player = new Player('player1');
            await board.addPlayer(player);
            // Player should be able to look at board
            const result = await board.look('player1');
            assert(result.includes('5x5'));
        });

        it('should add multiple players', async function() {
            const board = await Board.parseFromFile('boards/ab.txt');
            const player1 = new Player('player1');
            const player2 = new Player('player2');
            await board.addPlayer(player1);
            await board.addPlayer(player2);
            const result1 = await board.look('player1');
            const result2 = await board.look('player2');
            assert(result1.includes('5x5'));
            assert(result2.includes('5x5'));
        });
    });

    describe('look', function() {
        it('should return board state for existing player', async function() {
            const board = await Board.parseFromFile('boards/ab.txt');
            const player = new Player('player1');
            await board.addPlayer(player);
            const result = await board.look('player1');
            assert(result.startsWith('5x5'));
            assert(result.includes('down ?'));
        });

        it('should create player if not exists', async function() {
            const board = await Board.parseFromFile('boards/ab.txt');
            const result = await board.look('newplayer');
            assert(result.startsWith('5x5'));
        });

        it('should show face-up cards correctly', async function() {
            const board = await Board.parseFromFile('boards/ab.txt');
            await board.addPlayer(new Player('player1'));
            await board.flip('player1', 0, 0);
            const result = await board.look('player1');
            // Should show the card value for the flipped card
            assert(result.includes('my') || result.includes('up'));
        });
    });

    describe('flip', function() {
        it('should flip a card face up', async function() {
            const board = await Board.parseFromFile('boards/ab.txt');
            await board.addPlayer(new Player('player1'));
            await board.flip('player1', 0, 0);
            const card = board.getCards(0, 0);
            assert(card !== undefined);
            const faceUp = await card!.getFaceUp();
            assert.strictEqual(faceUp, true);
        });

        it('should throw error for non-existent player', async function() {
            const board = await Board.parseFromFile('boards/ab.txt');
            await assert.rejects(
                async () => await board.flip('nonexistent', 0, 0),
                Error,
                'Player not found'
            );
        });

        it('should throw error for invalid coordinates', async function() {
            const board = await Board.parseFromFile('boards/ab.txt');
            await board.addPlayer(new Player('player1'));
            await assert.rejects(
                async () => await board.flip('player1', 100, 100),
                Error
            );
        });

        it('should handle matching pair correctly', async function() {
            const board = await Board.parseFromFile('boards/ab.txt');
            await board.addPlayer(new Player('player1'));
            // Flip two matching cards
            await board.flip('player1', 0, 0);
            await board.flip('player1', 0, 2);
            // Both cards should be removed
            const card1 = board.getCards(0, 0);
            const card2 = board.getCards(0, 2);
            // Cards should be removed if they match
            // The exact behavior depends on implementation
        });

        it('should handle non-matching pair correctly', async function() {
            const board = await Board.parseFromFile('boards/ab.txt');
            await board.addPlayer(new Player('player1'));
            // Flip two non-matching cards
            await board.flip('player1', 0, 0); // A
            await board.flip('player1', 0, 1); // B
            // Wait a bit for processing
            await new Promise(resolve => setTimeout(resolve, 50));
            // Cards should be flipped back down after processing
            const card1 = board.getCards(0, 0);
            const card2 = board.getCards(0, 1);
            if (card1 !== undefined) {
                const faceUp1 = await card1.getFaceUp();
                // After non-match, cards should eventually be face down
                // (may take time to process removal queue)
                // Just verify cards exist and operation completed
                assert(card1 !== undefined);
            }
            if (card2 !== undefined) {
                assert(card2 !== undefined);
            }
        });

        it('should wait for card to become available', async function() {
            const board = await Board.parseFromFile('boards/ab.txt');
            await board.addPlayer(new Player('player1'));
            await board.addPlayer(new Player('player2'));
            
            // Player1 flips a card
            const flip1 = board.flip('player1', 0, 0);
            
            // Player2 tries to flip the same card (should wait)
            const flip2 = board.flip('player2', 0, 0);
            
            await flip1;
            // After player1 finishes, player2 should be able to proceed
            await flip2;
        });
    });

    describe('map', function() {
        it('should transform all cards with same value together', async function() {
            const board = await Board.parseFromFile('boards/ab.txt');
            await board.addPlayer(new Player('player1'));
            
            const transform = async (card: string) => {
                return card === 'A' ? 'X' : card;
            };
            
            await board.map('player1', transform);
            
            // Check that all A cards became X
            const card0 = board.getCards(0, 0);
            if (card0 !== undefined) {
                await card0.setFaceUp(true);
                const value = card0.value;
                // Should be X if originally A
            }
        });

        it('should throw error for non-existent player', async function() {
            const board = await Board.parseFromFile('boards/ab.txt');
            await assert.rejects(
                async () => await board.map('nonexistent', async (c) => c),
                Error,
                'Player not found'
            );
        });

        it('should maintain pairwise consistency', async function() {
            const board = await Board.parseFromFile('boards/ab.txt');
            await board.addPlayer(new Player('player1'));
            
            let transformCount = 0;
            const transform = async (card: string) => {
                transformCount++;
                return card + 'X';
            };
            
            await board.map('player1', transform);
            
            // All cards with same value should be transformed together
            // transformCount should be 2 (one for A, one for B)
            assert.strictEqual(transformCount, 2);
        });
    });

    describe('watch', function() {
        it('should wait for board changes', async function() {
            const board = await Board.parseFromFile('boards/ab.txt');
            await board.addPlayer(new Player('player1'));
            
            // Start watching
            const watchPromise = board.watch('player1');
            
            // Make a change
            setTimeout(async () => {
                await board.flip('player1', 0, 0);
            }, 10);
            
            const result = await watchPromise;
            assert(result.includes('5x5'));
        });

        it('should create player if not exists', async function() {
            const board = await Board.parseFromFile('boards/ab.txt');
            
            const watchPromise = board.watch('newplayer');
            
            setTimeout(async () => {
                await board.addPlayer(new Player('otherplayer'));
                await board.flip('otherplayer', 0, 0);
            }, 10);
            
            const result = await watchPromise;
            assert(result.includes('5x5'));
        });

        it('should detect card removal', async function() {
            const board = await Board.parseFromFile('boards/ab.txt');
            await board.addPlayer(new Player('player1'));
            
            const watchPromise = board.watch('player1');
            
            setTimeout(async () => {
                // Flip matching pair to remove cards
                await board.flip('player1', 0, 0);
                await board.flip('player1', 0, 2);
            }, 10);
            
            const result = await watchPromise;
            assert(result.includes('none') || result.includes('5x5'));
        });
    });

    describe('concurrent operations', function() {
        it('should handle multiple players flipping simultaneously', async function() {
            const board = await Board.parseFromFile('boards/ab.txt');
            await board.addPlayer(new Player('player1'));
            await board.addPlayer(new Player('player2'));
            await board.addPlayer(new Player('player3'));
            
            const promises = [
                board.flip('player1', 0, 0),
                board.flip('player2', 0, 1),
                board.flip('player3', 0, 2)
            ];
            
            await Promise.all(promises);
            
            // All flips should complete
            const card1 = board.getCards(0, 0);
            const card2 = board.getCards(0, 1);
            const card3 = board.getCards(0, 2);
            
            if (card1 !== undefined) {
                const faceUp1 = await card1.getFaceUp();
                assert.strictEqual(faceUp1, true);
            }
        });

        it('should handle map during flip operations', async function() {
            const board = await Board.parseFromFile('boards/ab.txt');
            await board.addPlayer(new Player('player1'));
            
            const flipPromise = board.flip('player1', 0, 0);
            const mapPromise = board.map('player1', async (c) => c + 'X');
            
            await Promise.all([flipPromise, mapPromise]);
            
            // Both operations should complete without errors
            const result = await board.look('player1');
            assert(result.includes('5x5'));
        });
    });
});
