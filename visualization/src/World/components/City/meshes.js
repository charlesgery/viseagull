import { Mesh } from 'https://unpkg.com/three@0.127.0/build/three.module.js';

import { createGeometries } from './geometries.js';
import { createBuildingMaterial, createCityGroundMaterial, createMaterials } from './materials.js';
import { getCityGroundDimensions } from './helpers.js'

const buildingBaseWidth = 10;
const buildingSpacing = buildingBaseWidth / 5;

function createMeshes(buildingsData, buildingSize) {

    const cityGroundDimensions = getCityGroundDimensions(buildingsData.length);

    const cityGroundWidth = cityGroundDimensions[0] * buildingBaseWidth + (cityGroundDimensions[0] + 1) * buildingSpacing;
    const cityGroundLength = cityGroundDimensions[1] * buildingBaseWidth + (cityGroundDimensions[1] + 1) * buildingSpacing;  

    const geometries = createGeometries(cityGroundWidth, cityGroundLength, buildingBaseWidth);
    // const materials = createMaterials(buildingsData);

    const cityGroundMaterial = createCityGroundMaterial();

    const cityGround = new Mesh(geometries.cityGround, cityGroundMaterial);
    cityGround.position.set(cityGroundWidth / 2, 0, cityGroundLength / 2);
    cityGround.rotation.x = - Math.PI / 2;
    cityGround.receiveShadow = true;
    cityGround.groundWidth = cityGroundWidth;
    cityGround.groundLength = cityGroundLength;

    var buildings = [];
    var buildingXPosition = buildingSpacing + buildingBaseWidth / 2;
    var buildingZPosition = buildingSpacing + buildingBaseWidth / 2;
    var buildingXNumber = 1;

    for(let i=0; i < buildingsData.length; i++){

        var buildingMaterial = createBuildingMaterial('base', null, null, null);
        const building = new Mesh(geometries.building, buildingMaterial.building);

        var heightScale;
        if (buildingSize.maxBuildingSize - buildingSize.minBuildingSize == 0){
            heightScale = 1
        }else {
            heightScale = (9 / (buildingSize.maxBuildingSize - buildingSize.minBuildingSize)) * buildingsData[i].height + (buildingSize.maxBuildingSize - 10 * buildingSize.minBuildingSize) / (buildingSize.maxBuildingSize - buildingSize.minBuildingSize);
        }

        
        // console.log(heightScale)

        building.scale.set(1, heightScale, 1);
        building.position.set(buildingXPosition, 10 * heightScale / 2, buildingZPosition);
        building.castShadow = true;
        building.fileName = buildingsData[i].fileName;
        building.initialColor = buildingMaterial.color;

        buildings.push(building);

        if(buildingXNumber % cityGroundDimensions[0] == 0){
            buildingXPosition = buildingSpacing + + buildingBaseWidth / 2
            buildingZPosition += buildingSpacing + buildingBaseWidth;
        }
        else{
            buildingXPosition += buildingSpacing + buildingBaseWidth;
        }

        buildingXNumber += 1;

    }

    return {
        cityGround,
        buildings
    };
}

export { createMeshes };