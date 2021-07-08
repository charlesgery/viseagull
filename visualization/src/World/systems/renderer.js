import { WebGLRenderer } from 'https://unpkg.com/three@0.127.0/build/three.module.js';

function createRenderer() {
  const renderer = new WebGLRenderer({ antialias: true });

  renderer.physicallyCorrectLights = true;
  renderer.shadowMap.enabled = true;

  return renderer;
}

export { createRenderer };
