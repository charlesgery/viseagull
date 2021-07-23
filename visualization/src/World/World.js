import { createCamera } from './components/camera.js';
import {
  createAxesHelper,
  createGridHelper,
} from './components/helpers.js';
import { createLights } from './components/lights.js';
import { createScene } from './components/scene.js';

import { City } from './components/City/City.js';
import { createGround } from './components/ground.js';
import { HUD } from './components/HUD/HUD.js'
import { Route } from './components/Route/Route.js'

import { createControls } from './systems/controls.js';
import { createRenderer } from './systems/renderer.js';
import { Resizer } from './systems/Resizer.js';
import { Loop } from './systems/Loop.js';
import { MouseRaycaster } from './systems/MouseRaycaster.js'

import { replaceCities } from './helpers/citiesLayout.js'

import { CameraHelper } from 'https://unpkg.com/three@0.127.0/build/three.module.js';
import { GUI } from './systems/GUI.js';
import { getMinMaxBuildingSize, getMinMaxDate } from './helpers/worldHelpers.js';

let camera;
let renderer;
let scene;
let loop;

class World {

  constructor(container, citiesData, routesData, commitToFiles, filesModificationsDates, urlToFiles) {


    // Creating system
    camera = createCamera();
    renderer = createRenderer();
    scene = createScene();
    loop = new Loop(camera, scene, renderer);
    container.append(renderer.domElement);

    const controls = createControls(camera, renderer.domElement);
    const { ambientLight, mainLight } = createLights();

    loop.updatables.push(controls);

    var buildingSize = getMinMaxBuildingSize(citiesData);

    var minMaxDate = getMinMaxDate(filesModificationsDates, "last_modification");


    var cities = [];
    for(let i=0; i < citiesData.length; i++){
      var city = new City(citiesData[i], buildingSize);
      cities.push(city);
      scene.add(city);
    }

    replaceCities(cities);


    // Routes
    var routes = [];
    var seenRoutes = [];
    for(let i=0; i < routesData.length; i++) {
      let routeStartLabel = routesData[i].route.start;
      let routeEndLabel = routesData[i].route.end;

      var routeLabels = [routeStartLabel, routeEndLabel];
      routeLabels = routeLabels.sort(function(a, b) {
        return a - b;
      });

      var isAlreadySeen = false;
      for (let i =0; i<seenRoutes.length; i++){
        if (seenRoutes[i][0] == routeLabels[0] && seenRoutes[i][1] == routeLabels[1]){
          isAlreadySeen = true;
        }
      }

      if (!isAlreadySeen) {

        seenRoutes.push(routeLabels);

        let firstCityIndex;
        let secondCityIndex;
  
        for (let j=0; j < cities.length; j++){
          if (cities[j].cityLabel == routeStartLabel){
            firstCityIndex = j;
          }
        }
        for (let j=0; j < cities.length; j++){
          if (cities[j].cityLabel == routeEndLabel){
            secondCityIndex = j;
          }
        }

        //if(cities[firstCityIndex].cityLabel == 21 && cities[secondCityIndex].cityLabel == 45){
          const route = new Route(cities[firstCityIndex], cities[secondCityIndex], routesData[i]);
          routes.push(route);
          scene.add(route);
        //}
        

      }
    }

    const ground = createGround();
    
    // Adding elements to the scene
    scene.add(ambientLight, mainLight, ground, camera);

    // Window Resizer
    const resizer = new Resizer(container, camera, renderer);

    // Axes
    scene.add(createAxesHelper(), createGridHelper());

    // Shadow Helper
    /*
    const helper = new CameraHelper( mainLight.shadow.camera );
    scene.add( helper );
    */


    // Mouse Raycaster
    this.mouseRaycaster = new MouseRaycaster(container, camera,commitToFiles, cities, urlToFiles);
    for(let i=0; i < cities.length; i++){
      for(let j=1; j < cities[i].children.length; j++){
        this.mouseRaycaster.add(cities[i].children[j], 'building');
      }
    }

    for(let i=0; i < routes.length; i++){
      this.mouseRaycaster.add(routes[i].children[0], 'road');
    }

    /*
    //HUD
    const hud = new HUD(camera, this.mouseRaycaster);
    loop.updatables.push(hud);
    */

    // GUI
    var gui = new GUI(cities, filesModificationsDates, this.mouseRaycaster, routes, scene);

    
  }

  render() {
    renderer.render(scene, camera);
  }

  start() {
    loop.start();
  }

  stop() {
    loop.stop();
  }

  highlightCommit(commit) {
    this.mouseRaycaster.updateHighlightedCommit(commit);
  }
}

export { World };
