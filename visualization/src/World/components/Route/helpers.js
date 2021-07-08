/* Check every possible direction (eg. NE, NS, ...) that is possible
Compute direction vector of the cities (eg. direction from north edge, to east edge)
Compare it to the baseline direction vector (NE in our case)
And keep the direction with the smallest difference with the baseline
*/

const possibleDirections = [
    ['N', 'S'],
    ['N', 'E'],
    ['N', 'W'],
    ['S', 'N'],
    ['S', 'E'],
    ['S', 'W'],
    ['E', 'N'],
    ['E', 'S'],
    ['E', 'W'],
    ['W', 'N'],
    ['W', 'S'],
    ['W', 'E'],
];

const north = [0, 1];
const south = [0, -1];
const east = [-1, 0];
const west = [1, 0];

function computeFacingDirections(firstCity, secondCity) {

    let firstCityCenterX = firstCity.position.x + firstCity.cityWidth / 2;
    let firstCityCenterY = firstCity.position.y + firstCity.cityLength / 2;
    
    let secondCityCenterX = secondCity.position.x + secondCity.cityWidth / 2;
    let secondCityCenterY = secondCity.position.y + secondCity.cityLength / 2;

    let directionX = secondCityCenterX - firstCityCenterX;
    let directionY = secondCityCenterY - firstCityCenterY;

    let magnitude = Math.sqrt(directionX**2 + directionY**2);
    directionX = directionX / magnitude;
    directionY = directionY / magnitude;

    let baseX = 1;
    let baseY = 0;

    let relativeAngle = Math.atan2(directionY, directionX) - Math.atan2(baseY, baseX);
    console.log('Relative Angle')
    console.log(relativeAngle);
    
    if (relativeAngle >= 0) {
        if (relativeAngle < Math.PI / 4) {
            return 'W';
        } else  if (relativeAngle < 3 * Math.PI / 4 ) {
            return 'N';
        } else {
            return 'E';
        }
    } else {
        if (relativeAngle > Math.PI / 4) {
            return 'W';
        } else if (relativeAngle > 3 * Math.PI / 4 ) {
            return 'S';
        } else {
            return 'E';
        }
    }

}

function computeStartingEndingPoints(city, cardinalDirection, routeWidth) {

    if (cardinalDirection == 'S') {
        var X = city.position.x + city.cityWidth / 2 - routeWidth / 2;
        var Y = city.position.z;
    } else if (cardinalDirection == 'N') {
        var X = city.position.x + city.cityWidth / 2 - routeWidth / 2;
        var Y = city.position.z + city.cityLength;
    } else if (cardinalDirection == 'E') {
        var X = city.position.x;
        var Y = city.position.z + city.cityLength / 2 - routeWidth / 2;
    } else {
        var X = city.position.x + city.cityWidth;
        var Y = city.position.z + city.cityLength / 2 - routeWidth / 2;
    }

    return { X, Y };

}

function getReverseDirection(cardinalDirection) {

    if (cardinalDirection == 'N') {
        return 'S';
    } else if (cardinalDirection == 'S') {
        return 'N';
    } else if (cardinalDirection == 'E') {
        return 'W';
    } else {
        return 'E';
    }
}

function computeBestDirection(startCity, endCity) {

    let smallestAngle = Math.PI;
    let bestDirection;

    for (let i = 0; i < possibleDirections.length; i++) {

        let startSide = possibleDirections[i][0];
        let endSide = possibleDirections[i][1];
        
        let baseDirection = computeBaseDirection(startSide, endSide);
        let direction = computeDirectionVector(startCity, endCity, startSide, endSide);


        let relativeAngle = Math.atan2(direction[1], direction[0]) - Math.atan2(baseDirection[1], baseDirection[0]);

        let angle = Math.abs(relativeAngle);


        if (angle < smallestAngle) {
            smallestAngle = angle;
            bestDirection = possibleDirections[i];
        }

    }

    return bestDirection;
}

function computeBaseDirection(startSide, endSide) {

    let startSideVector = getSideVector(startSide);
    let endSideVector = getSideVector(endSide);

    let baseDirectionX = startSideVector[0] - endSideVector[0];
    let baseDirectionY = startSideVector[1] - endSideVector[1];

    let magnitude = Math.sqrt(baseDirectionX**2 + baseDirectionY**2);

    baseDirectionX = baseDirectionX / magnitude;
    baseDirectionY = baseDirectionY / magnitude;

    const baseDirection = [baseDirectionX, baseDirectionY];

    return baseDirection;

}

function getSideVector(side) {

    if (side == 'N'){
        return north;
    }
    else if (side == 'S') {
        return south;
    }
    else if (side == 'E') {
        return east;
    }
    else {
        return west;
    }

}

function computeDirectionVector(startCity, endCity, startSide, endSide) {

    let startPoint = computePointLocation(startCity, startSide);
    let endPoint = computePointLocation(endCity, endSide);

    let directionX = endPoint[0] - startPoint[0];
    let directionY = endPoint[1] - startPoint[1];

    let magnitude = Math.sqrt(directionX**2 + directionY**2);

    directionX = directionX / magnitude;
    directionY = directionY / magnitude;

    return [directionX, directionY];

}

function computePointLocation(city, side) {

    var X;
    var Y;

    var positionZ;
    if (city.position.z > 100000){
        positionZ = 100000;
    }
    else {
        positionZ = city.position.z;
    }

    if (side == 'N') {
        X = city.position.x + city.cityWidth / 2;
        Y = positionZ + city.cityLength;
    }
    else if (side == 'S') {
        X = city.position.x + city.cityWidth / 2;
        Y = positionZ;
    }
    else if (side == 'E') {
        X = city.position.x;
        Y = positionZ + city.cityLength / 2;
    }
    else {
        X = city.position.x + city.cityWidth;
        Y = positionZ + city.cityLength / 2;
    }

    return [X, Y];

}

function isEdgeCase(directions) {
    if ((directions[0] == 'S' && directions[1] == 'W') ||
        (directions[0] == 'W' && directions[1] == 'S') ||
        (directions[0] == 'N' && directions[1] == 'E') ||
        (directions[0] == 'E' && directions[1] == 'N')) {
            return true;
        }
    else {
        return false;
    }
}

export { computeFacingDirections, computeStartingEndingPoints, getReverseDirection, computeBestDirection, isEdgeCase };