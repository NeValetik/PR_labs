/* Copyright (c) 2021-25 MIT 6.102/6.031 course staff, all rights reserved.
 * Redistribution of original or derived work requires permission of course staff.
 */

import assert from 'node:assert';
import fs from 'node:fs';
import { ICard, Card } from './card.js';
import { Player } from './player.js';
import { Deferred } from './deferred.js';

/**
 * TODO specification
 * Mutable and concurrency safe.
 */
export class Board {
    private readonly size: { row: number, col: number };
    private readonly cards: (ICard | undefined)[];
    private static instance: Board | null = null;
    private players: Player[] = [];
    private playerTurnStack: Map<Player, { row: number, col: number }[]> = new Map<Player, { row: number, col: number }[]>();
    // Queue for waiting players: key is "row,col", value is array of resolve functions
    private cardWaitQueue: Map<string, Array<() => void>> = new Map();
    // Queue for cards waiting to be removed (unmatched pairs)
    private removalQueue: Map<Player, { row: number, col: number }[]> = new Map<Player, { row: number, col: number }[]>();
    // Queue for watchers waiting for board changes
    private watchQueue: Array<() => void> = [];

    // Abstraction function:
    //   TODO
    // Representation invariant:
    //   TODO
    // Safety from rep exposure:
    //   TODO

    // TODO constructor
    constructor(size: { row: number, col: number }, cards: ICard[]) {
        if (Board.instance !== null) {
            throw new Error('Board already exists');
        }
        Board.instance = this;
        this.cards = cards;
        this.size = size;
        this.checkRep();
    }
    public async toString(): Promise<string> {
        const values = await Promise.all(this.cards.map(card => card?.getValue()));
        return values.join('\n');
    }

    // TODO checkRep

    private checkRep() {
        assert(this.size.row > 0 && this.size.col > 0, 'size must be positive');
        assert(this.cards.length === this.size.row * this.size.col, 'cards must be of size size * size');
    }
    // TODO other methods
    public getSize(): { row: number, col: number } {
        return this.size;
    }
    public async look(playerId: string): Promise<string> {
        let player = this.players.find(player => player.getId() === playerId);
        if (player === undefined) {
            await this.addPlayer(new Player(playerId));
            player = this.players.find(player => player.getId() === playerId);
        }
        if (player === undefined) {
            throw new Error('Failed to create or find player');
        }
        
        const size = this.getSize();
        const lines: string[] = [`${size.row}x${size.col}`];
        
        const playerCards = this.playerTurnStack.get(player) || [];
        
        for (let row = 0; row < size.row; row++) {
            for (let col = 0; col < size.col; col++) {
                const card = this.getCards(row, col);
                if (card === undefined) {
                    lines.push('none');
                    continue;
                }
                
                const faceUp = await card.getFaceUp();
                
                // Check if this card is controlled by this player (in their turn stack)
                const isControlledByPlayer = playerCards.some(pos => pos.row === row && pos.col === col);
                
                if (!faceUp) {
                    lines.push('down ?');
                } else if (isControlledByPlayer) {
                    const value = card.getValue();
                    lines.push(`my ${value || ''}`);
                } else {
                    const value = card.getValue();
                    lines.push(`up ${value || ''}`);
                }
            }
        }
        
        return lines.join('\n');
    }
    public getCards(): (ICard | undefined)[];
    public getCards(row: number, column: number): ICard | undefined;
    public getCards(row?: number, column?: number): (ICard | undefined)[] | ICard | undefined {
        if (row !== undefined && column !== undefined) {
            const card = this.cards[row * this.size.col + column];
            return card !== undefined ? card : undefined;
        }
        return this.cards;
    }

    private async removeCard(row: number, column: number): Promise<void> {
        this.cards[row * this.size.col + column] = undefined;
        // Notify waiting players that the card is now available (removed)
        this.notifyCardAvailable(row, column);
        // Notify watchers that board state changed
        this.notifyWatchers();
        return;
    }

    private notifyCardAvailable(row: number, column: number): void {
        const key = `${row},${column}`;
        const queue = this.cardWaitQueue.get(key);
        if (queue && queue.length > 0) {
            // Resolve the first waiting promise
            const resolve = queue.shift()!;
            resolve();
            // Clean up empty queues
            if (queue.length === 0) {
                this.cardWaitQueue.delete(key);
            }
        }
    }

    private notifyWatchers(): void {
        // Resolve all waiting watchers
        while (this.watchQueue.length > 0) {
            const resolve = this.watchQueue.shift()!;
            resolve();
        }
    }

    private async preprocessWaitForCardAvailable(player: Player, row: number, column: number): Promise<void> {
        const card = this.getCards(row, column);
        const stack = this.playerTurnStack.get(player);
        console.log(stack)
        if (stack === undefined || card === undefined) {
            return;
        }
        if (stack.length === 1) {
            const isBusy = await card.getIsBusy();
            console.log('isBusy', isBusy);
            const isBusyByMe = stack.some(pos => pos.row === row && pos.col === column);
            console.log('isBusyByMe', isBusyByMe);
            if (isBusyByMe) {
                return;
            }
            if (!isBusy) {
                return;
            }
            if (isBusy) {
                const pos = stack.shift()!;
                const removedCard = this.getCards(pos.row, pos.col);
                await removedCard?.setIsBusy(false);
                await this.removalQueue.get(player)?.push(pos);
                console.log('removalQueue', this.removalQueue.get(player));
                this.notifyCardAvailable(pos.row, pos.col);
                this.notifyWatchers();
                throw new Error('The card is not available');
            }
        }
    }

    private async waitForCardAvailable(row: number, column: number): Promise<void> {
        // Keep waiting until the card is available (not busy and exists)
        while (true) {
            const card = this.getCards(row, column);
            if (card === undefined) {
                // Card doesn't exist (was removed), don't wait
                return;
            }
            
            const isBusy = await card.getIsBusy();
            if (!isBusy) {
                // Card is available
                return;
            }

            // Card is busy, wait for notification
            const key = `${row},${column}`;
            const deferred = new Deferred<void>();
            if (!this.cardWaitQueue.has(key)) {
                this.cardWaitQueue.set(key, []);
            }
            this.cardWaitQueue.get(key)!.push(deferred.resolve);
            await deferred.promise;
            // After notification, loop again to check if card is actually available
        }
    }

    public static getInstance(): Board {
        if (Board.instance === null) {
            throw new Error('Board not initialized');
        }
        return Board.instance;
    }

    public async addPlayer(player: Player) {
        this.players.push(player);
        this.playerTurnStack.set(player, []);
        this.removalQueue.set(player, []);
        return this;
    }

    public async isBelongingToPlayer(card: ICard): Promise<boolean> {
        return card.getIsBusy();
    }

    private async processPreviousPair(player: Player): Promise<void> {
        const removalQueue = this.removalQueue.get(player);
        console.log(`removalQueue ${player.getId()}: ${JSON.stringify(removalQueue)}`);
        if (removalQueue !== undefined && removalQueue.length > 0) {
            while (removalQueue.length > 0) {
                const pos = removalQueue.shift()!;
                const card = this.getCards(pos.row, pos.col);
                if (card !== undefined && !(await card.getIsBusy())) {
                    await card.setFaceUp(false);
                    await card.setIsBusy(false);
                    this.notifyCardAvailable(pos.row, pos.col);
                }
            }
        }

        // Then process the current pair in the stack
        const stack = this.playerTurnStack.get(player);
        if (stack === undefined || stack.length < 2) {
            return;
        }

        const first = stack.shift()!;
        const second = stack.shift()!;
        const firstCard = this.getCards(first.row, first.col);
        const secondCard = this.getCards(second.row, second.col);
        if (firstCard === undefined || secondCard === undefined) {
            return;
        }

        await this.removeCard(first.row, first.col);
        await this.removeCard(second.row, second.col);
        // removeCard already notifies watchers
    }

    public async processRemovalQueue(row: number, column: number): Promise<void> {
        if (this.removalQueue !== undefined) {
            while (this.removalQueue.entries().some(([_, positions]) => positions.some((pos) => pos.row === row && pos.col === column))) {
                for (const [_, positions] of this.removalQueue.entries()) {
                    const index = positions.findIndex((pos) => pos.row === row && pos.col === column);
                    if (index !== -1) {
                        positions.splice(index, 1);
                    }
                }
            }
        }
    }

    public async processStack(player: Player, row?: number, column?: number): Promise<void> {
        const stack = this.playerTurnStack.get(player);
        // console.log(stack)
        if (stack === undefined) {
            return;
        }

        if (stack.length < 2) {
            // Need at least 2 cards to process a pair
            return;
        }

        const first = stack.shift()!;
        const second = stack.shift()!;
        const firstCard = this.getCards(first.row, first.col);
        const secondCard = this.getCards(second.row, second.col);
        if (firstCard === undefined || secondCard === undefined) {
            return;
        }
        const firstValue = firstCard.getValue();
        const secondValue = secondCard.getValue();

        if (firstValue !== secondValue) {
            // Unmatched pair: add to removal queue instead of unshifting back to stack
            const removalQueue = this.removalQueue.get(player);
            
            if (removalQueue !== undefined) {
                removalQueue.push(first);
                removalQueue.push(second);
            }
        
            await firstCard.setIsBusy(false);
            await secondCard.setIsBusy(false);
            this.notifyCardAvailable(first.row, first.col);
            this.notifyCardAvailable(second.row, second.col);
        } else {
            stack.unshift({row: first.row, col: first.col});
            stack.unshift({row: second.row, col: second.col});
        }
        return;
    }

    public async flip(playerId: string, row: number, column: number): Promise<void> {
        const player = this.players.find(player => player.getId() === playerId);
        if (player === undefined) {
            throw new Error('Player not found');
        }
        const stack = this.playerTurnStack.get(player);
        const removalQueue = this.removalQueue.get(player);
        const isTheSecondCard = stack?.length === 1;

        if (isTheSecondCard) {
            console.log('isTheSecondCard', row, column);
            await this.preprocessWaitForCardAvailable(player, row, column);
        }
        
        await this.waitForCardAvailable(row, column);
        
        if (stack !== undefined && stack.length >= 2 || (removalQueue !== undefined && removalQueue.length >= 1)) {
            await this.processPreviousPair(player);
        }
        
        await this.waitForCardAvailable(row, column);
        const card = this.getCards(row, column);
        if (card === undefined) {
            throw new Error('Card not found');
        }
        
        const isBusy = await card.getIsBusy();
        if (isBusy) {
            // Card became busy again (race condition), wait once more
            await this.waitForCardAvailable(row, column);
            const finalCard = this.getCards(row, column);
            if (finalCard === undefined) {
                throw new Error('Card not found');
            }
            await finalCard.setFaceUp(true);
            await finalCard.setIsBusy(true);
            await this.playerTurnStack.get(player)?.push({ row, col: column });
        } else {
            await card.setFaceUp(true);
            await card.setIsBusy(true);
            await this.playerTurnStack.get(player)?.push({ row, col: column });
        }

        await this.processRemovalQueue(row, column);
        
        await this.processStack(player);
        // Notify watchers that board state changed
        this.notifyWatchers();
        return;
    }

    public async map(playerId: string, f: (card: string) => Promise<string>): Promise<void> {
        const player = this.players.find(player => player.getId() === playerId);
        if (player === undefined) {
            throw new Error('Player not found');
        }

        // Group all cards by their current value to maintain pairwise consistency
        // Cards with the same value must be transformed together
        const valueToCards = new Map<string, Array<{ card: ICard, row: number, col: number }>>();
        
        const size = this.getSize();
        for (let row = 0; row < size.row; row++) {
            for (let col = 0; col < size.col; col++) {
                const card = this.getCards(row, col);
                if (card === undefined) {
                    continue;
                }
                // Access the actual value regardless of face-up state
                // ICard interface has value as a property (typed as string, so always defined)
                const cardValue = card.value;
                
                if (!valueToCards.has(cardValue)) {
                    valueToCards.set(cardValue, []);
                }
                valueToCards.get(cardValue)!.push({ card, row, col });
            }
        }

        // Transform each unique value and apply to all cards with that value
        // This ensures matching pairs remain matching during transformation
        const transformPromises: Promise<void>[] = [];
        
        for (const [value, cards] of valueToCards.entries()) {
            // Create a promise that transforms all cards with this value
            const transformPromise = (async () => {
                const newValue = await f(value);
                // Apply the transformation to all cards with this value
                for (const { card } of cards) {
                    await card.setValue(newValue);
                }
            })();
            transformPromises.push(transformPromise);
        }

        // Wait for all transformations to complete
        // This allows interleaving: other operations can run between transformations
        // of different values, but all cards with the same value are transformed atomically
        await Promise.all(transformPromises);

        // Notify watchers that board state changed
        this.notifyWatchers();
        return;
    }

    public async watch(playerId: string): Promise<string> {
        // Ensure player exists
        let player = this.players.find(player => player.getId() === playerId);
        if (player === undefined) {
            await this.addPlayer(new Player(playerId));
            player = this.players.find(player => player.getId() === playerId);
        }
        if (player === undefined) {
            throw new Error('Failed to create or find player');
        }

        // Take a snapshot of the current board state
        const snapshot = await this.getBoardSnapshot();

        // Wait for a change notification
        while (true) {
            const deferred = new Deferred<void>();
            this.watchQueue.push(deferred.resolve);
            await deferred.promise;

            // Check if the board state actually changed
            const currentState = await this.getBoardSnapshot();
            if (this.hasBoardChanged(snapshot, currentState)) {
                // Board changed, return the new state
                return await this.look(playerId);
            }
            // No actual change detected, wait again
        }
    }

    private async getBoardSnapshot(): Promise<Map<string, { faceUp: boolean, value: string | undefined, exists: boolean }>> {
        const snapshot = new Map<string, { faceUp: boolean, value: string | undefined, exists: boolean }>();
        const size = this.getSize();
        
        for (let row = 0; row < size.row; row++) {
            for (let col = 0; col < size.col; col++) {
                const key = `${row},${col}`;
                const card = this.getCards(row, col);
                if (card === undefined) {
                    snapshot.set(key, { faceUp: false, value: undefined, exists: false });
                } else {
                    const faceUp = await card.getFaceUp();
                    const value = faceUp ? card.getValue() : undefined;
                    snapshot.set(key, { faceUp, value, exists: true });
                }
            }
        }
        return snapshot;
    }

    private hasBoardChanged(
        oldSnapshot: Map<string, { faceUp: boolean, value: string | undefined, exists: boolean }>,
        newSnapshot: Map<string, { faceUp: boolean, value: string | undefined, exists: boolean }>
    ): boolean {
        // Check if any card changed
        for (const [key, oldState] of oldSnapshot.entries()) {
            const newState = newSnapshot.get(key);
            if (newState === undefined) {
                // Card position disappeared (shouldn't happen, but check anyway)
                return true;
            }
            
            // Check if card was removed or added
            if (oldState.exists !== newState.exists) {
                return true;
            }
            
            // Check if face up/down status changed
            if (oldState.faceUp !== newState.faceUp) {
                return true;
            }
            
            // Check if value changed (only if both are face up)
            if (oldState.faceUp && newState.faceUp && oldState.value !== newState.value) {
                return true;
            }
        }
        
        // Check for new cards (shouldn't happen in normal operation, but check anyway)
        for (const key of newSnapshot.keys()) {
            if (!oldSnapshot.has(key)) {
                return true;
            }
        }
        
        return false;
    }
    /**
     * Make a new board by parsing a file.
     * 
     * PS4 instructions: the specification of this method may not be changed.
     * 
     * @param filename path to game board file
     * @returns a new board with the size and cards from the file
     * @throws Error if the file cannot be read or is not a valid game board
     */
    public static async parseFromFile(filename: string): Promise<Board> {
        const file = await fs.promises.readFile(filename, 'utf8');
        const [rawSize, ...cards] = file.split('\n').map(line => line.trim()).filter(line => line !== '');
        const [row, col] = rawSize?.split("x") || [];
        if (row === undefined || col === undefined) {
            throw new Error('invalid size');
        }
        return new Board({ row: parseInt(row), col: parseInt(col) }, cards.map(card => new Card(card, false, false)));
    }
}
