import { Group, Shape, Path, BufferGeometry, LineBasicMaterial, Line, ExtrudeGeometry, MeshStandardMaterial, Mesh } from 'https://unpkg.com/three@0.127.0/build/three.module.js';
import { computeBestDirection, computeFacingDirections, computeStartingEndingPoints, getReverseDirection, isEdgeCase } from './helpers.js';

let routeWidth = 5;

class Route extends Group {
  constructor(firstCity, secondCity, routeData) {
    super();

    const shape = new Shape();

    let bestDirection = computeBestDirection(firstCity, secondCity);
    
    let startingPoints = computeStartingEndingPoints(firstCity, bestDirection[0], routeWidth);
    let endingPoints = computeStartingEndingPoints(secondCity, bestDirection[1], routeWidth);

    if(isEdgeCase(bestDirection)) {
        if (bestDirection[1] == 'E' || bestDirection[1] == 'W') {
            endingPoints.Y += routeWidth;
        } else {
            endingPoints.X += routeWidth;
        }
    }

    let startingX = startingPoints.X;
    let startingY = startingPoints.Y;
    let endingX = endingPoints.X;
    let endingY = endingPoints.Y;

    shape.moveTo(startingX, startingY);
    shape.quadraticCurveTo((startingX + endingX) / 2, (startingY + endingY) / 2, endingX, endingY);


    if(isEdgeCase(bestDirection)) {
        if (bestDirection[1] == 'N'){
            shape.lineTo(endingX - routeWidth, endingY);
        } else if (bestDirection[1] == 'S'){
            shape.lineTo(endingX - routeWidth, endingY);
        } else if (bestDirection[1] == 'W'){
            shape.lineTo(endingX, endingY - routeWidth);
        } else if (bestDirection[1] == 'E'){
            shape.lineTo(endingX, endingY - routeWidth);
        }
    } else {
        if (bestDirection[1] == 'N'){
            shape.lineTo(endingX + routeWidth, endingY);
        } else if (bestDirection[1] == 'S'){
            shape.lineTo(endingX + routeWidth, endingY);
        } else if (bestDirection[1] == 'W'){
            shape.lineTo(endingX, endingY + routeWidth);
        } else if (bestDirection[1] == 'E'){
            shape.lineTo(endingX, endingY + routeWidth);
        }
    }

    if (bestDirection[0] == 'N'){
        shape.quadraticCurveTo((startingX + endingX + 2 * routeWidth) / 2, (startingY + endingY - 2 * routeWidth) / 2, startingX + routeWidth, startingY);
    } else if (bestDirection[0] == 'S'){
        shape.quadraticCurveTo((startingX + endingX + 2 * routeWidth) / 2, (startingY + endingY - 2 * routeWidth) / 2, startingX + routeWidth, startingY);
    } else if (bestDirection[0] == 'W'){
        shape.quadraticCurveTo((startingX + endingX) / 2, (startingY + endingY + 2 * routeWidth) / 2, startingX, startingY + routeWidth);
    } else if (bestDirection[0] == 'E'){
        shape.quadraticCurveTo((startingX + endingX) / 2, (startingY + endingY + 2 * routeWidth) / 2, startingX, startingY + routeWidth);
    }

    shape.lineTo(startingX, startingY);

    const extrudeSettings = {
        steps: 2,
        depth: 2.5,
        bevelEnabled: false,
        bevelThickness: 1,
        bevelSize: 1,
        bevelOffset: 0,
        bevelSegments: 1
    };
    
    const geometry = new ExtrudeGeometry( shape, extrudeSettings );
    const material = new MeshStandardMaterial( { color: 'grey' } );
    const mesh = new Mesh( geometry, material ) ;

    mesh.rotation.set(Math.PI / 2, 0, 0);
    mesh.position.set(0, 2.5, 0)

    mesh.firstCityLabel = firstCity.cityLabel;
    mesh.secondCityLabel = secondCity.cityLabel;

    mesh.initialColor = 'grey';

    mesh.routeWidth = routeData.width;

    this.add( mesh );



  }

}

export { Route };