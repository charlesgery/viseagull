// Duplicated code with City/meshes.js
// Find a way to refactor that
const buildingBaseWidth = 10;
const buildingSpacing = buildingBaseWidth / 5;

function replaceCities(cities){

    let maxIterations = 300;
    let numberIterations = 0;
    let alpha = 0.01;
    let numIntersectedCities = 0;

    var initialDistancesBetweenCities = computeInitialDistances(cities);

    do {

        numIntersectedCities = 0;

        for(let i=0; i < cities.length; i++){


            let intersectedCities = intersectsCities(i, cities);
            numIntersectedCities += intersectedCities.length;

            if (intersectedCities.length > 0){

                let forces = computeForces(i, cities, intersectedCities, initialDistancesBetweenCities);

                cities[i].position.x += alpha * forces[0];
                cities[i].position.z += alpha * forces[1];

            }
    
        }

        numberIterations += 1;

    } while (numIntersectedCities > 0 && numberIterations < maxIterations)
    

}

function intersectsCities(index, cities){

    var intersectedCities = [];

    for(let i=0; i<cities.length; i++){
        if(i != index){
            if (intersectsCity(index, i, cities)){
                intersectedCities.push(cities[i]);
            }
        }
    }

    return intersectedCities;

}

function intersectsCity(i, j, cities){


    

    let firstCityOriginX = cities[i].position.x - 2 * buildingBaseWidth; 
    let firstCityOriginY = cities[i].position.z - 2 * buildingBaseWidth;
    let firstCityWidth = cities[i].cityWidth;
    let firstCityLength = cities[i].cityLength;

    let secondCityOriginX = cities[j].position.x; 
    let secondCityOriginY = cities[j].position.z;
    let secondCityWidth = cities[j].cityWidth;
    let secondCityLength = cities[j].cityLength;

    let hoverlap = (firstCityOriginX < secondCityOriginX + secondCityWidth) && (secondCityOriginX < firstCityOriginX + firstCityWidth + 4 * buildingBaseWidth);
    let voverlap = (firstCityOriginY < secondCityOriginY + secondCityLength) && (secondCityOriginY < firstCityOriginY + (firstCityLength + 4 * buildingBaseWidth));


    return hoverlap && voverlap;
}

function computeInitialDistances(cities) {

    var initialDistancesBetweenCities = {};

    for (let i=0; i<cities.length; i++){

        let firstCityOriginX = cities[i].position.x; 
        let firstCityOriginY = cities[i].position.z;
        let firstCityWidth = cities[i].cityWidth;
        let firstCityLength = cities[i].cityLength;
        let firstCityCenterX = firstCityOriginX + firstCityWidth / 2;
        let firstCityCenterY = firstCityOriginY + firstCityLength / 2;
    
        for (let j=i+1; j<cities.length; j++) {
    
            let secondCityOriginX = cities[j].position.x; 
            let secondCityOriginY = cities[j].position.z;
            let secondCityWidth = cities[j].cityWidth;
            let secondCityLength = cities[j].cityLength;
            let secondCityCenterX = secondCityOriginX + secondCityWidth / 2;
            let secondCityCenterY = secondCityOriginY + secondCityLength / 2;

            let distanceBetweenCitiesX = secondCityCenterX - firstCityCenterX;
            let distanceBetweenCitiesY = secondCityCenterY - firstCityCenterY;

            if (i in initialDistancesBetweenCities){
                initialDistancesBetweenCities[i][j] = [distanceBetweenCitiesX, distanceBetweenCitiesY];
            } else {
                initialDistancesBetweenCities[i]= {};
                initialDistancesBetweenCities[i][j] = [distanceBetweenCitiesX, distanceBetweenCitiesY];
            }
            
            
        }
    }

    return initialDistancesBetweenCities;
    
}

function computeForces(index, cities, intersectedCities, initialDistancesBetweenCities) {
    
    // Compute Spring Forces
    let springForces = [0, 0];

    let firstCityOriginX = cities[index].position.x; 
    let firstCityOriginY = cities[index].position.z;
    let firstCityWidth = cities[index].cityWidth;
    let firstCityLength = cities[index].cityLength;
    let firstCityCenterX = firstCityOriginX + firstCityWidth / 2;
    let firstCityCenterY = firstCityOriginY + firstCityLength / 2;

    for (let i=0; i<cities.length; i++) {
        if (index != i) {

            let secondCityOriginX = cities[i].position.x; 
            let secondCityOriginY = cities[i].position.z;
            let secondCityWidth = cities[i].cityWidth;
            let secondCityLength = cities[i].cityLength;
            let secondCityCenterX = secondCityOriginX + secondCityWidth / 2;
            let secondCityCenterY = secondCityOriginY + secondCityLength / 2;

            let distanceBetweenCitiesX = secondCityCenterX - firstCityCenterX;
            let distanceBetweenCitiesY = secondCityCenterY - firstCityCenterY;
            let springStiffness = 1;

            let initialDistanceX;
            let initialDistanceY;

            if (index < i){
                initialDistanceX = initialDistancesBetweenCities[index][i][0];
                initialDistanceY = initialDistancesBetweenCities[index][i][1];
            } else {
                initialDistanceX = initialDistancesBetweenCities[i][index][0];
                initialDistanceY = initialDistancesBetweenCities[i][index][1];
            }

            springForces[0] += - springStiffness * (distanceBetweenCitiesX - initialDistanceX);
            springForces[1] += - springStiffness * (distanceBetweenCitiesY - initialDistanceY);


        }
    }

    // Repulsion Forces
    let repulsionForces = [0, 0];

    for (let i=0; i<intersectedCities.length; i++) {

        let secondCityOriginX = intersectedCities[i].position.x; 
        let secondCityOriginY = intersectedCities[i].position.z;
        let secondCityWidth = intersectedCities[i].cityWidth;
        let secondCityLength = intersectedCities[i].cityLength;
        let secondCityCenterX = secondCityOriginX + secondCityWidth / 2;
        let secondCityCenterY = secondCityOriginY + secondCityLength / 2;

        let distanceBetweenCitiesX = secondCityCenterX - firstCityCenterX;
        let distanceBetweenCitiesY = secondCityCenterY - firstCityCenterY;

        if (distanceBetweenCitiesX == 0) distanceBetweenCitiesX = 1;
        if (distanceBetweenCitiesY == 0) distanceBetweenCitiesY = 1;

        let repulsionFactor = 100;

        let repulsionX = - repulsionFactor * 1 / distanceBetweenCitiesX;
        let repulsionY = - repulsionFactor * 1 / distanceBetweenCitiesY;



        repulsionForces[0] += - repulsionX;
        repulsionForces[1] += - repulsionY;
    }

    let forces = [springForces[0] + repulsionForces[0], springForces[1] + repulsionForces[1]];

    return forces;
}

export { replaceCities };