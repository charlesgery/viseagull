import { BoxBufferGeometry, CylinderBufferGeometry } from 'https://unpkg.com/three@0.127.0/build/three.module.js';


function createGeometries(cityGroundWidth, cityGroundLength, buildingBaseWidth) {
 

    const cityGround = new BoxBufferGeometry(cityGroundWidth, cityGroundLength, 5);

    const building = new BoxBufferGeometry(buildingBaseWidth, buildingBaseWidth, buildingBaseWidth);

    return {
        cityGround,
        building,
    };
}

export { createGeometries };