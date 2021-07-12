import { Raycaster, Vector2 } from 'https://unpkg.com/three@0.127.0/build/three.module.js';

const setSize = (container, camera, renderer) => {
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
  
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
  };
  
  class MouseRaycaster {
    constructor(container, camera, commitToFiles) {

        const raycaster = new Raycaster();
        const mouse = new Vector2(1, 1);

        this.trackedObjects = [];
        this["Hovered Element Information"] = "";
        this.commitToFiles = commitToFiles;
        this.highlightedCommit = null;
  
        window.addEventListener('mousemove', (event) => {


            mouse.x = ( event.clientX / container.offsetWidth ) * 2 - 1;
    	    mouse.y = - ( event.clientY / container.offsetHeight ) * 2 + 1;

            raycaster.setFromCamera(mouse, camera);

            var minDistance = -1;
            var closestObject = null;
            for(let i=0; i<this.trackedObjects.length; i++){
                const intersects = raycaster.intersectObject(this.trackedObjects[i].object);
                if (intersects.length !== 0) {
                    let obj = intersects[0].object;
                    let distance = intersects[0].distance;
                    if(distance <= minDistance || minDistance < 0){
                        minDistance = distance;
                        closestObject = obj;
                    }
                }
            }

            for(let i=0; i<this.trackedObjects.length; i++){
                if (closestObject != null && this.trackedObjects[i].object.uuid == closestObject.uuid) {
                    this.trackedObjects[i].object.material.color.set(0xffff00)

                    if (this.trackedObjects[i].tag == 'building'){
                        this["Hovered Element Information"] = this.trackedObjects[i].object.fileName;
                    }
                    else if (this.trackedObjects[i].tag == 'road'){
                        this["Hovered Element Information"] = this.trackedObjects[i].object.firstCityLabel + ' to ' + this.trackedObjects[i].object.secondCityLabel + '. Width :' + this.trackedObjects[i].object.routeWidth;
                    }

                }
                else{
                    if (this.highlightedCommit != null && this.highlightedCommit in this.commitToFiles){
                        var isInCommit = false;
                        for (let j=0; j<this.commitToFiles[this.highlightedCommit].length; j++){
                            if (this.commitToFiles[this.highlightedCommit][j] == this.trackedObjects[i].object.fileName){
                                isInCommit = true;
                            }
                        }
                        if (isInCommit){
                            this.trackedObjects[i].object.material.color.set('blue');
                        } else {
                            this.trackedObjects[i].object.material.color.set('darkslategray'); 
                        }
                    } else {
                        this.trackedObjects[i].object.material.color.set(this.trackedObjects[i].object.initialColor);
                    }
                    
                }
            }
            
 
        });
    }

    add(object, tag){
        this.trackedObjects.push({object: object, tag: tag});
    }

    updateHighlightedCommit(commit) {
        this.highlightedCommit = commit;
    }


  }
  
  export { MouseRaycaster };