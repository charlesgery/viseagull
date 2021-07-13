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

    var p1 = {x: startingX, y: startingY};
    var p2 = {x: endingX, y: endingY};

    // Compute arc values
    // https://www.ryanjuckett.com/biarc-interpolation/
    var t1;
    if (bestDirection[0] == 'N') t1 = {x: 0, y:1};
    else if (bestDirection[0] == 'S') t1 = {x: 0, y:-1};
    else if (bestDirection[0] == 'E') t1 = {x: -1, y:0};
    else if (bestDirection[0] == 'W') t1 = {x: 1, y:0};

    var t2;
    if (bestDirection[1] == 'N') t2 = {x: 0, y:-1};
    else if (bestDirection[1] == 'S') t2 = {x: 0, y:1};
    else if (bestDirection[1] == 'E') t2 = {x: 1, y:0};
    else if (bestDirection[1] == 'W') t2 = {x: -1, y:0};

    var v = {x: endingX - startingX, y: endingY - startingY};
    var t = {x: t1.x + t2.x, y: t1.y + t2.y};


    var d1, d2;
    if (t1.x == t2.x && t1.y == t2.y) {
        d1  = (v.x ** 2 + v.y ** 2) / (4 * (v.x * t2.x + v.y * t2.y));
        d2 = d1;
    } else {
        d1 = (-(v.x * t.x + v.y * t.y) + Math.sqrt((v.x * t.x + v.y * t.y)**2 + 2 * (1 - (t1.x * t2.x + t1.y * t2.y)) * (v.x ** 2 + v.y ** 2))) / (2 * (1 - (t1.x * t2.x + t1.y * t2.y)));
        d2 = d1;
    }

    
    //var d2 = (0.5 * (v.x * v.x + v.y * v.y) - d1 * (v.x * t1.x + v.y * t1.y)) / (v.x * t2.x + v.y * t2.y - d1 * (t1.x * t2.x + t1.y * t2.y - 1))


    var pm = {x:0, y:0}
    pm.x = (startingX + d1 * t1.x) * (d2/(d1 + d2)) + (endingX - d2 * t2.x) * (d1/(d1+d2));
    pm.y = (startingY + d1 * t1.y) * (d2/(d1 + d2)) + (endingY - d2 * t2.y) * (d1/(d1+d2));

    var n1 = {x:-t1.y, y:t1.x};
    var c1 = {x:0, y:0};
    var s1 = (((pm.x - startingX) ** 2 + (pm.y - startingY) ** 2) / (2 * (n1.x * (pm.x - startingX) + n1.y * (pm.y - startingY))))
    c1.x = p1.x + s1 * n1.x;
    c1.y = p1.y + s1 * n1.y;
    var r1 = Math.abs(s1);

    var n2 = {x:-t2.y, y:t2.x};
    var c2 = {x:0, y:0};
    var s2 = (((pm.x - endingX) ** 2 + (pm.y - endingY) ** 2) / (2 * (n2.x * (pm.x - endingX) + n2.y * (pm.y - endingY))))
    c2.x = p2.x + s2 * n2.x;
    c2.y = p2.y + s2 * n2.y;
    var r2 = Math.abs(s2);

    var op1 = {x: (startingX-c1.x)/r1, y: (startingY-c1.y)/r1};
    var om1 = {x: (pm.x - c1.x)/r1, y: (pm.y - c1.y)/r1};
    var op2 = {x: (endingX - c2.x)/r2, y: (endingY - c2.y)/r2};
    var om2 = {x: (pm.x - c2.x)/r2, y: (pm.y -c2.y)/r2};

    function crossLikeProduct(a, b){
        return a.x * b.y - a.y * b.x;
    }

    var theta1;
    if (d1 > 0 && crossLikeProduct(op1, om1) > 0){
        theta1 = Math.acos(op1.x * om1.x + op1.y * om1.y);
    } else if (d1 > 0 && crossLikeProduct(op1, om1) <= 0){
        theta1 = - Math.acos(op1.x * om1.x + op1.y * om1.y);
    } else if (d1 <= 0 && crossLikeProduct(op1, om1) > 0){
        theta1 = -2 * Math.PI + Math.acos(op1.x * om1.x + op1.y * om1.y);
    } else if (d1 <= 0 && crossLikeProduct(op1, om1) <= 0){
        theta1 = 2 * Math.PI - Math.acos(op1.x * om1.x + op1.y * om1.y);
    }

    var theta2;
    if (d2 > 0 && crossLikeProduct(op2, om2) > 0){
        theta2 = Math.acos(op2.x * om2.x + op2.y * om2.y);
    } else if (d2 > 0 && crossLikeProduct(op2, om2) <= 0){
        theta2 = - Math.acos(op2.x * om2.x + op2.y * om2.y);
    } else if (d2 <= 0 && crossLikeProduct(op2, om2) > 0){
        theta2 = -2 * Math.PI + Math.acos(op2.x * om2.x + op2.y * om2.y);
    } else if (d2 <= 0 && crossLikeProduct(op2, om2) <= 0){
        theta2 = 2 * Math.PI - sMath.acos(op2.x * om2.x + op2.y * om2.y);
    }


    var firstCityCenter = firstCity.getCityCenter();
    var secondCityCenter = secondCity.getCityCenter();


    shape.moveTo(startingX, startingY);

    var firstClockwise;
    var firstArcAngle1, firstArcAngle2;
    var firstRadiusUpdate;

    if (bestDirection[0] == 'N'){
        if (c1.x > firstCityCenter.x) {
            firstClockwise = true;
            firstArcAngle1 = Math.PI;
            firstArcAngle2 = Math.PI + theta1;
            firstRadiusUpdate = - routeWidth;
        } else {
            firstClockwise = false;
            firstArcAngle1 = 0;
            firstArcAngle2 = theta1;
            firstRadiusUpdate = routeWidth;
        }
    } else if (bestDirection[0] == 'S') {
        if (c1.x > firstCityCenter.x) {
            firstClockwise = false;
            firstArcAngle1 = Math.PI;
            firstArcAngle2 = Math.PI + theta1;
            firstRadiusUpdate = - routeWidth;
        } else {
            firstClockwise = true;
            firstArcAngle1 = 0
            firstArcAngle2 = theta1;
            firstRadiusUpdate = routeWidth;
        }
    } else if (bestDirection[0] == 'E') {
        if (c1.y > firstCityCenter.y) {
            firstClockwise = true;
            firstArcAngle1 = 3 * Math.PI / 2;
            firstArcAngle2 = 3 * Math.PI / 2 + theta1;
            firstRadiusUpdate = - routeWidth;
        } else {
            firstClockwise = false;
            firstArcAngle1 = Math.PI / 2;
            firstArcAngle2 = Math.PI / 2 + theta1;
            firstRadiusUpdate = routeWidth;
        }
    } else if (bestDirection[0] == 'W') {
        if (c1.y > firstCityCenter.y) {
            firstClockwise = false;
            firstArcAngle1 = 3 * Math.PI / 2;
            firstArcAngle2 = 3 * Math.PI / 2 + theta1;
            firstRadiusUpdate = - routeWidth;
        } else {
            firstClockwise = true;
            firstArcAngle1 = Math.PI / 2;
            firstArcAngle2 = Math.PI / 2 + theta1;
            firstRadiusUpdate = routeWidth;
        }
    }
    shape.absarc(c1.x, c1.y, r1, firstArcAngle1, firstArcAngle2, firstClockwise);

    var secondClockwise;
    var secondArcAngle1, secondArcAngle2;
    var secondRadiusUpdate;

    if (bestDirection[1] == 'N'){
        if (c2.x > secondCityCenter.x) {
            secondClockwise = false;
            secondArcAngle1 = Math.PI + theta2;
            secondArcAngle2 = Math.PI;
            secondRadiusUpdate = - routeWidth;
        } else {
            secondClockwise = true;
            secondArcAngle1 = theta2;
            secondArcAngle2 = 0;
            secondRadiusUpdate = + routeWidth;
        }
    } else if (bestDirection[1] == 'S'){
        if (c2.x > secondCityCenter.x) {
            secondClockwise = true;
            secondArcAngle1 = Math.PI + theta2;
            secondArcAngle2 = Math.PI;
            secondRadiusUpdate = - routeWidth;
        } else {
            secondClockwise = false;
            secondArcAngle1 = theta2;
            secondArcAngle2 = 0;
            secondRadiusUpdate = routeWidth;
        }
    } else if (bestDirection[1] == 'E'){
        if (c2.y > secondCityCenter.y) {
            secondClockwise = false;
            secondArcAngle1 = 3 * Math.PI / 2 + theta2;
            secondArcAngle2 = 3 * Math.PI / 2;
            secondRadiusUpdate = - routeWidth;
        } else {
            secondClockwise = true;
            secondArcAngle1 = Math.PI / 2 + theta2;
            secondArcAngle2 = Math.PI / 2;
            secondRadiusUpdate = routeWidth;
        }
    } else if (bestDirection[1] == 'W'){
        if (c2.y > secondCityCenter.y) {
            secondClockwise = true;
            secondArcAngle1 = 3 * Math.PI / 2 + theta2;
            secondArcAngle2 = 3 * Math.PI / 2;
            secondRadiusUpdate = - routeWidth;
        } else {
            secondClockwise = false;
            secondArcAngle1 = Math.PI / 2 + theta2;
            secondArcAngle2 = Math.PI / 2;
            secondRadiusUpdate = routeWidth;
        }
    }
    shape.absarc(c2.x, c2.y, r2, secondArcAngle1, secondArcAngle2, secondClockwise);


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
        secondRadiusUpdate = - secondRadiusUpdate;
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

    shape.absarc(c2.x, c2.y, r2 + secondRadiusUpdate, secondArcAngle2, secondArcAngle1, !secondClockwise)
    shape.absarc(c1.x, c1.y, r1 + firstRadiusUpdate, firstArcAngle2, firstArcAngle1, !firstClockwise)

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