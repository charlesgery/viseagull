import { DirectionalLight, HemisphereLight } from 'https://unpkg.com/three@0.127.0/build/three.module.js';

function createLights() {
  
  const ambientLight = new HemisphereLight(
    'white',
    'darkslategrey',
    3,
  );

  const mainLight = new DirectionalLight('white', 2, 100);
  mainLight.position.set(200, 200, 200);
  mainLight.castShadow = true;

  //Set up shadow properties for the light
  mainLight.shadow.camera.left = 500; // default
  mainLight.shadow.camera.right = -500; // default
  mainLight.shadow.camera.top = 1000; // default
  mainLight.shadow.camera.bottom = -200; // default
  mainLight.shadow.camera.near = 0.5; // default
  mainLight.shadow.camera.far = 1500; // default

  return { ambientLight, mainLight };
}

export { createLights };
