export class Player {
  constructor(public id: string) {
    this.id = id;
  }
  public getId(): string {
    return this.id;
  }
}