import SensorGrammarVisitor from "./lib/SensorGrammarVisitor.js";
import Product from "./spl/Product.js";
import {
  TileLayer,
  GeoJSONLayer,
  Map,
  GeoJSONLayerStyle,
  StaticIntervalsStyle,
} from "./spl/Map.js";
import { getPropertyParams } from "./SensorVisitorHelper.js";

class Visitor extends SensorGrammarVisitor {
  constructor(store, debug) {
    super();
    this.store = store;
    this.debug = debug || false;
  }

  log(msg) {
    if (this.debug) {
      console.log(msg);
    }
  }

  start(ctx) {
    return this.visitParse(ctx);
  }

  visitParse(ctx) {
    this.log(`visitParse: ${ctx.getText()}`);
    return super.visitParse(ctx);
  }

  // --------   PRODUCT  --------
  visitCreateProduct(ctx) {
    const gisName = ctx.getChild(1).getText();
    const srid = ctx.getChild(3).getText();
    this.log(`visitCreateGIS: ${gisName}`);
    this.store.setProduct(new Product(gisName, srid));

    // CREATE BASE STYLES
    const baseStyles = [
      new GeoJSONLayerStyle("redPoint", "#FF0000", "#FF0000", 1, 1),
      new GeoJSONLayerStyle("greenPoint", "#008000", "#008000", 1, 1),
      new GeoJSONLayerStyle("grayPoint", "#808080", "#808080", 1, 1),
      new GeoJSONLayerStyle("orangePoint", "#FFA500", "#FFA500", 1, 1),
      new GeoJSONLayerStyle("redPolygon", "#FF0000", "#FF0000", 0.5, 1),
      new GeoJSONLayerStyle("greenPolygon", "#008000", "#008000", 0.5, 1),
      new GeoJSONLayerStyle("grayPolygon", "#808080", "#808080", 0.5, 1),
      new GeoJSONLayerStyle("orangePolygon", "#FFA500", "#FFA500", 0.5, 1),
    ];
    baseStyles.forEach((style) => this.store.getProduct().addStyle(style));
  }

  // --------   SENSOR GROUPS  --------
  visitCreateSensorGroup(ctx) {
    const sensorName = ctx.getChild(1).getText();

    let index = 3;
    const sensors = [];
    while (index < ctx.getChildCount()) {
      const sensor = ctx.getChild(index).getText();
      if (sensor == ";") break;
      sensors.push(sensor);
      index += 2;
    }

    this.store.getProduct().addSensorGroup(sensorName, sensors);
  }

  // --------   DIMENSIONS  --------
  visitCreateSpatialDimension(ctx) {
    const dimensionName = ctx.getChild(2).getText();

    if (this.store.getDimension(dimensionName) != null) {
      throw `Dimension ${dimensionName} already exists!`;
    }

    if (ctx.getChild(4).getText().toUpperCase() != "GEOMETRY") {
      throw `Dimension ${dimensionName} is not a spatial dimension!`;
    }

    const dimGeomType = ctx.getChild(6).getText();
    const parsedGemType =
      dimGeomType.charAt(0).toUpperCase() + dimGeomType.slice(1).toLowerCase();

    // Adds to dimension and to entities
    this.store.addSpatialDimension(dimensionName, parsedGemType);
    this.store.setCurrentDimension(dimensionName);

    super.visitCreateSpatialDimension(ctx);
    this.store.setCurrentDimension(null);
    this.store.setCurrentEntity(null);
  }

  visitCreateDimensionProperties(ctx) {
    super.visitCreateDimensionProperties(ctx);
  }

  visitCreateCategoricalDimension(ctx) {
    const dimensionName = ctx.getChild(2).getText();

    if (this.store.getDimension(dimensionName) != null) {
      throw `Dimension ${dimensionName} already exists!`;
    }

    if (ctx.getChild(0).getText().toUpperCase() != "CATEGORICAL") {
      throw `Dimension ${dimensionName} is not a categorical dimension!`;
    }

    const propField = ctx.getChild(6).getText();
    this.store.addCategoricalDimension(dimensionName, propField);
    this.store.setCurrentDimension(dimensionName);

    super.visitCreateCategoricalDimension(ctx);

    this.store.setCurrentDimension(null);
  }

  visitDimPropertyDefinition(ctx) {
    const propertyName = ctx.getChild(0).getText();
    const propertyType = ctx.getChild(1).getText();
    const hasDisplayString = ctx.getChildCount() == 3;

    const dimProps = {
      id: propertyName,
      type: propertyType,
      displayString: hasDisplayString ? ctx.getChild(2).getText() : null,
    };

    if (dimProps.displayString == null) {
      delete dimProps.displayString;
    }

    this.store.getCurrentEntity().addProperty(
      propertyName,
      propertyType,
      getPropertyParams(
        ctx.children
          .slice(2)
          .filter((s) => s.getSymbol)
          .map((s) => s.getSymbol().text.toLowerCase())
      )
    );

    this.store.getCurrentDimension().properties.push(dimProps);
    super.visitDimPropertyDefinition(ctx);
  }

  // DIMENSIONS PARENT
  visitCreateParentDimension(ctx) {
    const dimensionName = ctx.getChild(3).getText();

    const parentDim = this.store.getDimension(dimensionName);

    if (parentDim == null) {
      throw `Dimension ${dimensionName} not found!`;
    }

    // this.store.getCurrentDimension().parent = parentDim;

    // Create relationship between current entity and parent dimension
    const sourceOpts = {
      label: "belongs",
      multiplicity: "0..1",
    };
    const targetOpts = {
      label: "contains",
      multiplicity: "0..*",
    };
    const rSource = this.store.getCurrentEntity().name;
    const rTarget = parentDim.id;

    this.store
      .getProduct()
      .addRelationship(rSource, rTarget, sourceOpts, targetOpts);

    super.visitCreateParentDimension(ctx);
    this.store.setCurrentDimension(null);
  }

  // --------   RANGES  --------
  visitCreateRange(ctx) {
    const rangeName = ctx.getChild(1).getText();

    this.store.addRange(rangeName);
    this.store.setCurrentRange(rangeName);
    super.visitCreateRange(ctx);

    this.store.setCurrentRange(null);
  }

  visitRangeProperty(ctx) {
    let rangeProps = {};
    const range = this.store.getCurrentRange();
    const hasToSymbol = ctx.getChild(1).getText() == "TO";

    if (hasToSymbol) {
      const hasColor = ctx.getChildCount() == 7;
      const color = hasColor ? ctx.getChild(6).getText() : "#808080";
      rangeProps = {
        minValue: ctx.getChild(0).getText(),
        maxValue: ctx.getChild(2).getText(),
        label: ctx.getChild(4).getText().replace(/['"]+/g, ""),
        color: hasColor ? ctx.getChild(6).getText() : null,
        style: new GeoJSONLayerStyle(
          range.id + "-" + ctx.getChild(4).getText().replace(/['"]+/g, ""),
          color,
          color,
          1,
          1
        ),
      };
    } else {
      // Does not have TO symbol
      const hasColor = ctx.getChildCount() == 5;
      const color = hasColor ? ctx.getChild(4).getText() : "#808080";
      rangeProps = {
        value: ctx.getChild(0).getText(),
        label: ctx.getChild(2).getText().replace(/['"]+/g, ""),
        color: hasColor ? ctx.getChild(4).getText() : null,
        style: new GeoJSONLayerStyle(
          range.id + "-" + ctx.getChild(2).getText().replace(/['"]+/g, ""),
          color,
          color,
          1,
          1
        ),
      };
    }

    if (rangeProps.color == null) {
      delete rangeProps.color;
    }

    range.properties.push(rangeProps);
    super.visitRangeProperty(ctx);
  }

  // --------   SENSORS  --------
  visitCreateSensor(ctx) {
    const isMoving = ctx.getChild(0).getText() == "MOVING";
    const sensorName = isMoving
      ? ctx.getChild(2).getText()
      : ctx.getChild(1).getText();
    const sensorInterval = isMoving
      ? parseInt(ctx.getChild(6).getText())
      : parseInt(ctx.getChild(5).getText());
    const sensorGeom = isMoving
      ? ctx.getChild(10).getText()
      : ctx.getChild(9).getText();

    this.store
      .getProduct()
      .addSensor(sensorName, sensorInterval, isMoving, sensorGeom);

    this.store.setCurrentSensor(sensorName);
    super.visitCreateSensor(ctx);

    this.store.setCurrentSensor(null);
  }

  visitCreateSensorProperties(ctx) {
    const sensor = this.store.getCurrentSensor();

    // ADD ENTITY AND SET ID AND GEOMETRY
    this.store.getProduct().addEntity(sensor.entity);
    this.store.setCurrentEntity(sensor.entity);
    this.store
      .getCurrentEntity()
      .addProperty(
        "id",
        "Long",
        getPropertyParams(["identifier", "required", "unique"])
      );

    if (!this.store.getCurrentSensor().isMoving) {
      this.store.getCurrentEntity().addProperty("geometry", sensor.geom);
    }

    // ADD ENTITY FOR MEASUREMENTS
    // Create relationship between current entity and measurement entity
    const sourceOpts = {
      label: "sensors",
      multiplicity: "0..*",
    };
    const targetOpts = {
      label: "sensor_id",
      multiplicity: "0..1",
    };
    const rSource = this.store.getCurrentSensor().entity;
    const rTarget = this.store.getCurrentSensor().id + "Measurement";

    this.store
      .getProduct()
      .addRelationship(rSource, rTarget, sourceOpts, targetOpts);

    this.store.getProduct().addEntity(sensor.id + "Measurement");
    this.store.setCurrentEntity(sensor.id + "Measurement");
    this.store
      .getCurrentEntity()
      .addProperty(
        "id",
        "Long",
        getPropertyParams(["identifier", "required", "unique"])
      );

    if (this.store.getCurrentSensor().isMoving) {
      this.store.getCurrentEntity().addProperty("geometry", sensor.geom);
    }

    this.store
      .getCurrentEntity()
      .addProperty("date", "DateTime", getPropertyParams(["required"]));

    this.store
      .getProduct()
      .addRelationship(rSource, rTarget, sourceOpts, targetOpts);

    this.store.setCurrentEntity(sensor.entity);

    // ADD BASE LAYER AND SENSOR LAYER
    const { id, defaultMap } = sensor;

    const map = new Map(defaultMap, id + " Map");

    const baseLayer = new TileLayer(
      "base",
      "base",
      "http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
    );

    map.addLayer({
      name: "base",
      baseLayer: true,
      selected: true,
      order: 0,
    });

    // try to find previous base layer, if exists dont add
    if (this.store.getProduct().getLayer("base") == null)
      this.store.getProduct().addLayer(baseLayer);

    const layer = new GeoJSONLayer(
      sensor.defaultLayer,
      sensor.isMoving ? sensor.factTableEntity : sensor.entity,
      sensor.isMoving ? sensor.factTableEntity : sensor.entity + "-geometry",
      false,
      "grayPoint"
    );

    // if its null or empty array, add default styles
    if (layer.availableStyles == null || layer.availableStyles.length == 0) {
      layer.availableStyles = [
        "greenPoint",
        "grayPoint",
        "redPoint",
        "orangePoint",
        "greenPolygon",
        "grayPolygon",
        "redPolygon",
        "orangePolygon",
      ];
    }
    map.addLayer({
      name: sensor.defaultLayer,
      baseLayer: false,
      style: "grayPoint",
      selected: true,
      order: 1,
    });

    // try to find previous layer, if exists dont add
    if (this.store.getProduct().getLayer(sensor.defaultLayer) == null) {
      this.store.getProduct().addLayer(layer);
    }

    // ADD MAP
    this.store.getProduct().addMap(defaultMap, map);

    super.visitCreateSensorProperties(ctx);

    this.store.setCurrentEntity(null);
  }

  visitSensorPropertyDefinition(ctx) {
    const pName = ctx.getChild(0).getText();
    this.log(`visitPropertyDefinition: ${pName}`);
    const pType = ctx.getChild(1).getText();

    this.store.getCurrentEntity().addProperty(
      pName,
      pType,
      getPropertyParams(
        ctx.children
          .slice(2)
          .filter((s) => s.getSymbol)
          .map((s) => s.getSymbol().text.toLowerCase())
      )
    );
  }

  // SENSOR WITH SPATIAL DIMENIONS  --------
  visitAddSpatialDimensionToSensor(ctx) {
    const sensor = this.store.getCurrentSensor();
    const dimRelName = ctx.getChild(3).getText();

    // iterate all dimensions
    let index = 5;
    while (index < ctx.getChildCount()) {
      const dimName = ctx.getChild(index).getText();
      const dim = this.store.getDimension(dimName);

      if (dim == null) {
        throw `Dimension ${dimName} not found!`;
      }

      // Add to sensor dimensions
      if (sensor.dimensions.find((d) => d.id == dimRelName) == null) {
        sensor.dimensions.push({
          id: dimRelName,
          type: "SPATIAL",
          entities: [dimName],
        });
      } else {
        sensor.dimensions
          .find((d) => d.id == dimRelName)
          .entities.push(dimName);
      }

      // Add dimension to entity
      // Create relationship between current entity and measurement entity
      const sourceOpts = {
        label: dimName.toLowerCase() + "_id",
        multiplicity: "0..1",
      };
      const targetOpts = {
        label: this.store.getCurrentSensor().entity,
        multiplicity: "0..*",
      };
      const rSource = this.store.getCurrentSensor().entity;
      const rTarget = dimName;

      if (!this.store.getCurrentSensor().isMoving) {
        this.store
          .getProduct()
          .addRelationship(rSource, rTarget, sourceOpts, targetOpts);
      }

      // Addd layer to map
      const layer = new GeoJSONLayer(
        dim.id,
        dim.id,
        dim.id + "-geometry",
        false,
        dim.geomType == "Point" ? "grayPoint" : "grayPolygon"
      );

      // ADD styles for each sensor property
      if (layer.availableStyles == null || layer.availableStyles.length == 0) {
        layer.availableStyles = ["grayPolygon"];
      }
      sensor.measureData.forEach((measure) => {
        layer.availableStyles.push(measure.name);
        if (dim.geomType == "Polygon" || dim.geomType == "Geometry")
          layer.availableStyles.push(measure.name + "_POLYGON");
      });

      const map = this.store.getProduct().getMap(sensor.defaultMap);
      map.addLayer({
        name: dim.id,
        baseLayer: false,
        style: dim.geomType == "Point" ? "grayPoint" : "grayPolygon",
        selected: false,
        order: map.layers.length,
      });

      // try to find previous layer, if exists dont add
      if (this.store.getProduct().getLayer(dim.id) == null) {
        this.store.getProduct().addLayer(layer);
      } else {
        // if exists, push the available styles and remove duplicates
        this.store
          .getProduct()
          .getLayer(dim.id)
          .availableStyles.push(...layer.availableStyles);

        this.store.getProduct().getLayer(dim.id).availableStyles = [
          ...new Set(this.store.getProduct().getLayer(dim.id).availableStyles),
        ];
      }

      index += 2;
    }
  }

  // SENSOR WITH CATEGORICAL DIMENIONS  --------
  visitAddCategoricalDimensionToSensor(ctx) {
    const sensor = this.store.getCurrentSensor();

    let dimGroup = ctx.getChild(3).getText();
    let index = 5;

    if (dimGroup == "(") {
      index = 4;
      dimGroup = null;
    }

    while (index < ctx.getChildCount()) {
      // CHECK IF DIMENSION EXISTS
      const dimName = ctx.getChild(index).getText();
      const dim = this.store.getDimension(dimName);

      if (dim == null) {
        throw `Dimension ${dimName} not found!`;
      }

      // Check if has custom ranges
      const hasCustomRanges = ctx.getChild(index + 1).getText() == "RANGE";

      const dimToAdd = {
        id: dimName,
        type: "CATEGORICAL",
        field: dim.field,
        groupId: dimGroup,
      };

      if (dimGroup == null) delete dimToAdd.groupId;

      if (hasCustomRanges) {
        const rangeName = ctx.getChild(index + 2).getText();
        const range = this.store.getRange(rangeName);

        if (range == null) {
          throw `Range ${rangeName} not found!`;
        }

        dimToAdd.categories = range.properties.map((prop) => {
          const from =
            prop.minValue == "-Infinity"
              ? prop.minValue
              : parseFloat(prop.minValue);
          const to =
            prop.maxValue == "Infinity"
              ? prop.maxValue
              : parseFloat(prop.maxValue);

          const finalObj = {
            value: prop.value,
            from: isNaN(from) ? null : from,
            to: isNaN(to) ? null : to,
            label: prop.label,
          };

          if (finalObj.value == null) delete finalObj.value;
          if (finalObj.from == null) delete finalObj.from;
          if (finalObj.to == null) delete finalObj.to;

          return finalObj;
        });
      }

      sensor.addDimension(dimToAdd);

      // Add dimension to entity
      this.store.getCurrentEntity().addProperty(
        dimToAdd.field,
        dimToAdd.categories ? "Double" : "String",
        getPropertyParams(
          ctx.children
            .slice(index + 2)
            .filter((s) => s.getSymbol)
            .map((s) => s.getSymbol().text.toLowerCase())
        )
      );

      index += hasCustomRanges ? 4 : 2;
    }
  }

  // SENSOR MEASUREMENTS  --------
  visitCreateSensorMeasurementData(ctx) {
    super.visitCreateSensorMeasurementData(ctx);
  }

  visitCreateMeasurementProperty(ctx) {
    const sensor = this.store.getCurrentSensor();
    this.store.setCurrentEntity(sensor.id + "Measurement");

    const sensorProps = {};
    const sensorName = ctx.getChild(0).getText().toLowerCase();
    const sensorType = ctx.getChild(1).getText();

    if (ctx.getChildCount() > 2) {
      let index = 2;
      while (index < ctx.getChildCount()) {
        const property = ctx.getChild(index).getText();
        const value = ctx.getChild(index + 1).getText();

        if (property === "UNITS") {
          // replace quotes, "" and '' quotes
          sensorProps.units = value.replace(/["']/g, "");
          index += 2;
        } else if (property === "ICON") {
          sensorProps.icon = value.replace(/["']/g, "");
          index += 2;
        } else if (property === "RANGE") {
          sensorProps.range = value.replace(/["']/g, "");
          index += 2;
        } else {
          index += 2;
        }
      }

      sensor.addMeasureData({
        name: sensorName,
        type: sensorType,
        ...sensorProps,
      });

      // Add property to entity
      this.store.getCurrentEntity().addProperty(
        sensorName,
        sensorType,
        getPropertyParams(
          ctx.children
            .slice(2)
            .filter((s) => s.getSymbol)
            .map((s) => s.getSymbol().text.toLowerCase())
        )
      );
    } else {
      sensorProps.name = sensorName;
      sensorProps.type = sensorType;
      sensor.addMeasureData(sensorProps);

      // Add property to entity
      this.store.getCurrentEntity().addProperty(
        sensorName,
        sensorType,
        getPropertyParams(
          ctx.children
            .slice(2)
            .filter((s) => s.getSymbol)
            .map((s) => s.getSymbol().text.toLowerCase())
        )
      );
    }

    // Add styles to layer
    const layer = this.store.getProduct().getLayer(sensor.defaultLayer);
    layer.availableStyles.push(sensorName);

    // ADD STYLES FOR EACH MEASURE DATA
    // IF HAS CUSTOM RANGES, NEED TO ADD TO AVAILABLE STYLES
    const customRange = this.store.getRange(sensorProps.range);
    if (customRange) {
      // ADD TO LAYER AVAILABLE STYLES
      customRange.properties.forEach((range) => {
        this.store.getProduct().addStyle(range.style);
      });

      const styleNames = [
        {
          name: sensorName,
          property: "data." + sensorName,
          type: "Point",
        },
        {
          name: sensorName + "_POLYGON",
          property: "data." + sensorName,
          type: "Polygon",
        },
      ];

      styleNames.forEach((sensorStyle) => {
        this.store.getProduct().addStyle(
          new StaticIntervalsStyle(
            sensorStyle.name,
            sensorStyle.property,
            customRange.properties
              .filter((range) => range.value != "DEFAULT")
              .map((range) => {
                const minValue =
                  range.minValue == "-Infinity"
                    ? range.minValue
                    : parseFloat(range.minValue);
                const maxValue =
                  range.maxValue == "Infinity"
                    ? range.maxValue
                    : parseFloat(range.maxValue);

                if (range.value != null) {
                  return {
                    value: range.value,
                    label: range.label,
                    style: range.style.name,
                  };
                }
                return {
                  minValue: minValue,
                  maxValue: maxValue,
                  label: range.label,
                  style: range.style.name,
                };
              }),
            customRange.properties
              .filter((range) => range.value == "DEFAULT")
              .map((range) => range.style.name)[0]
          )
        );
      });
    } else {
      const styleNames = [
        {
          name: sensorName,
          property: "data." + sensorName,
          type: "Point",
        },
        {
          name: sensorName + "_POLYGON",
          property: "data." + sensorName,
          type: "Polygon",
        },
      ];

      styleNames.forEach((sensorStyle) => {
        this.store.getProduct().addStyle(
          new StaticIntervalsStyle(
            sensorStyle.name,
            sensorStyle.property,
            [
              {
                minValue: "-Infinity",
                maxValue: 20,
                style:
                  sensorStyle.type == "Point" ? "greenPoint" : "greenPolygon",
              },
              {
                minValue: 20,
                maxValue: 40,
                style:
                  sensorStyle.type == "Point" ? "orangePoint" : "orangePolygon",
              },
              {
                minValue: 40,
                maxValue: "Infinity",
                style: sensorStyle.type == "Point" ? "redPoint" : "redPolygon",
              },
            ],
            sensorStyle.type == "Point" ? "grayPoint" : "grayPolygon"
          )
        );
      });
    }
    super.visitCreateMeasurementProperty(ctx);
  }

  // SENSOR MAP BBOX  --------
  visitAddBBXToSensor(ctx) {
    const sensor = this.store.getCurrentSensor();

    const hasBracket = ctx.getChild(3).getText() == "[";

    const [lat, lon] = hasBracket
      ? ctx.getChild(4).getText().split(",")
      : ctx.getChild(3).getText().split(",");

    const zoom = hasBracket
      ? ctx.getChild(7).getText()
      : ctx.getChild(5).getText();

    const map = this.store.getProduct().getMap(sensor.defaultMap);
    map.setCenter(lat, lon, zoom);
  }

  /* ****************** Deployment ************************ */

  visitDeploymentProperty(ctx) {
    this.log(`visitDeploymentProperty`);
    this.store
      .getProduct()
      .addDeploymentProperty(
        ctx.getChild(0).getText().slice(1, -1),
        ctx.getChild(1).getText().slice(1, -1)
      );
  }
}

export default Visitor;
