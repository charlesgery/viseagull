import { MeshStandardMaterial } from 'https://unpkg.com/three@0.127.0/build/three.module.js';

function createMaterials(buildingsData) {
  const cityGround = new MeshStandardMaterial({
    color: 'grey',
  });

  var buildings = []
  for(let i=0; i < buildingsData.length; i++){
      const building = new MeshStandardMaterial({
        color: 'darkslategray',
      });
    buildings.push(building)
  }

  return { cityGround, buildings };
}

function createCityGroundMaterial() {
  const cityGround = new MeshStandardMaterial({
    color: 'grey',
  });

  return cityGround;
}

function createBuildingMaterial(dateType, fileName, filesModificationsDates, minMaxDate) {

  var building;
  var color;
  if (dateType == "last_modification" && fileName in filesModificationsDates){

    var date = new Date(filesModificationsDates[fileName][dateType]);
    var timestamp = date.getTime();

    var colorHue = (360 - 230) * (timestamp - minMaxDate.min) / (minMaxDate.max - minMaxDate.min) + 230;

    color = `hsl(${colorHue}, 100%, 50%)`;

    building = new MeshStandardMaterial({
      color: color,
    });

  } else if (dateType == "creation_date" && fileName in filesModificationsDates){
    var date = new Date(filesModificationsDates[fileName][dateType]);
    var timestamp = date.getTime();

    var colorHue = (360 - 230) * (timestamp - minMaxDate.min) / (minMaxDate.max - minMaxDate.min) + 230;

    color = `hsl(${colorHue}, 100%, 50%)`;

    building = new MeshStandardMaterial({
      color: color,
    });

  }
  else {

    color = 'darkslategray';

    building = new MeshStandardMaterial({
      color: 'darkslategray',
    });
  }

  return {building, color};
}

export { createMaterials, createCityGroundMaterial, createBuildingMaterial };
