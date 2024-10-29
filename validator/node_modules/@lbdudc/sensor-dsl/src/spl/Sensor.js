export default class Sensor {
  constructor(id, interval, moving, geom) {
    if (!id) {
      throw `Sensor ID cannot be null`;
    }

    this.id = id;
    this.entity = id + "Entity";
    this.defaultMap = id.toLowerCase() + "-map";
    this.defaultLayer = id.toLowerCase() + "-layer";
    this.time = interval || 1000;
    this.isMoving = moving || false;
    this.factTableEntity = id + "Measurement";
    this.geom = geom || "Point";
    this.measureData = [];
    this.dimensions = [];
  }

  addDimension(dimension) {
    this.dimensions.push(dimension);
  }

  addMeasureData(measureData) {
    this.measureData.push(measureData);
  }
}
