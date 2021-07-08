import { Texture, MeshBasicMaterial, PlaneGeometry, Mesh, Group } from 'https://unpkg.com/three@0.127.0/build/three.module.js';

class HUD extends Group {
  constructor(camera, mouseRaycaster) {
    super();

    this.camera = camera;
    this.mouseRaycaster = mouseRaycaster;

    // Code from StatsVR library : https://github.com/Sean-Bradley/StatsVR/blob/master/src/client/statsvr.ts
    this.canvas = document.createElement("canvas");
    this.canvas.width = 256;
    this.canvas.height = 256;

    this.ctx = this.canvas.getContext("2d");
    this.texture = new Texture(this.canvas);
    const material = new MeshBasicMaterial({
      map: this.texture,
      depthTest: false,
      transparent: true,
    });
    const geometry = new PlaneGeometry(2, 2, 2, 2);

    this.statsPlane = new Mesh(geometry, material);
    this.statsPlane.position.x = -3.0;
    this.statsPlane.position.y = 2.0;
    this.statsPlane.position.z = -10;
    this.statsPlane.renderOrder = 9999;

    this.camera.add(this.statsPlane);

  }

  tick(delta) {
    this.texture.needsUpdate = true;
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    this.ctx.strokeStyle = "#035363";
    for (var i = 0; i < 256; i++) {
        this.ctx.beginPath();
        this.ctx.moveTo(i, 16);
        this.ctx.lineTo(i, 0);
        this.ctx.stroke();
    }

    if (this.mouseRaycaster.hoveredObjectData != null){
        this.ctx.font = "13px Calibri";
        this.ctx.fillStyle = "#00cc00";
        this.ctx.fillText(this.mouseRaycaster.hoveredObjectData, 1, 13);
    }

    }

}

export { HUD };