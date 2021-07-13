import { Group } from 'https://unpkg.com/three@0.127.0/build/three.module.js';
import { createBuildingMaterial } from './materials.js';

import { createMeshes } from './meshes.js';

class City extends Group {
  constructor(cityData, buildingSize) {
    super();
 

    this.meshes = createMeshes(cityData.buildings, buildingSize);
    //this.updateColor(filesModificationsDates, minMaxDate, 'last_modification');

    this.position.set(cityData.centroid.x * 200, 0, cityData.centroid.y * 200)

    this.cityWidth = this.meshes.cityGround.groundWidth;
    this.cityLength = this.meshes.cityGround.groundLength;

    this.cityLabel = cityData.cityLabel;

    this.add(
      this.meshes.cityGround,
    );

    for (let i=0; i<this.meshes.buildings.length; i++){
        this.add(this.meshes.buildings[i]);
    }

  }

  updateColor(filesModificationsDates, minMaxDate, dateType) {

    for (let i=0; i<this.meshes.buildings.length; i++){

      var buildingMaterial = createBuildingMaterial(dateType, this.meshes.buildings[i].fileName, filesModificationsDates, minMaxDate);
      this.meshes.buildings[i].initialColor = buildingMaterial.color;

      this.meshes.buildings[i].material = buildingMaterial.building;
    }
  }

  getCityCenter(){
    return {x: this.position.x + this.cityWidth / 2, y: this.position.z + this.cityLength / 2};
  }

}

export { City };