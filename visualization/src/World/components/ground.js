import { PlaneBufferGeometry, MeshStandardMaterial, Mesh } from 'https://unpkg.com/three@0.127.0/build/three.module.js';

function createGround() {

    const geometry = new PlaneBufferGeometry(3000, 3000);
    const material = new MeshStandardMaterial({color: "green"});

    const ground = new Mesh(geometry, material);
    ground.receiveShadow = true;

    ground.rotation.x = - Math.PI / 2;

    return ground;
}

export {createGround};