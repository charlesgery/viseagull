import { PerspectiveCamera } from 'https://unpkg.com/three@0.127.0/build/three.module.js';

function createCamera() {
  const camera = new PerspectiveCamera(35, 1, 1, 10000);

  camera.position.set(0, 700, 0);

  return camera;
}

export { createCamera };
