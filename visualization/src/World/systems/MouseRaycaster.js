import { Raycaster, Vector2 } from 'https://unpkg.com/three@0.127.0/build/three.module.js';

const setSize = (container, camera, renderer) => {
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
  
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
  };
  
  class MouseRaycaster {
    constructor(container, camera, commitToFiles, cities) {

        const raycaster = new Raycaster();
        const mouse = new Vector2(1, 1);

        this.cities = cities;

        this.trackedObjects = [];
        this.hardColored = {};

        this["Hovered Element Information"] = "";
        this.commitToFiles = commitToFiles;
        this.highlightedCommit = null;

        window.addEventListener('click', (event) => {

            var closestObject = this.getClosestObject(event, mouse, container, raycaster, camera);
            var clickedOnBuilding = false;

            for(let i=0; i<this.trackedObjects.length; i++){


                if (closestObject != null && this.trackedObjects[i].object.uuid == closestObject.uuid) {

                    // reset hard coded
                    // ajouter un variable hard colored pour pas changer ce qui a été colorié suite a un clic
                    if (this.trackedObjects[i].tag == 'building'){

                        this.resetHardColored()
                        
                        clickedOnBuilding = true;
                        var parentCityLabel = this.trackedObjects[i].object.parent.cityLabel;
                        
                        for (let j=0; j<this.cities.length; j++){
                            if (this.cities[j].cityLabel == parentCityLabel){
                                this.cities[j].meshes.cityGround.material.color.set(0xffff00);
                                this.hardColored[this.cities[j].meshes.cityGround.uuid] = true;
                            }
                        }

                        for(let j=0; j<this.trackedObjects.length; j++){
                            if (this.trackedObjects[j].tag == 'road'){
                                if (this.trackedObjects[j].object.firstCityLabel == parentCityLabel || this.trackedObjects[j].object.secondCityLabel == parentCityLabel){
                                    this.trackedObjects[j].object.material.color.set(0xffff00);
                                    this.hardColored[this.trackedObjects[j].object.uuid] = true;
                                }
                            }
                        }

                    } 
                    
                }
            }

            if (!clickedOnBuilding) {
                // set all elements to their initial color
                this.resetHardColored()
            }



        })
  
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

            var firstHighlightedCity = null;
            var secondHighlightedCity = null;
            for(let i=0; i<this.trackedObjects.length; i++){


                if (closestObject != null && this.trackedObjects[i].object.uuid == closestObject.uuid) {

                    if (this.trackedObjects[i].tag == 'building' || this.trackedObjects[i].tag == 'road'){
                        this.trackedObjects[i].object.material.color.set(0xffff00)

                        if (this.trackedObjects[i].tag == 'building'){
                            this["Hovered Element Information"] = this.trackedObjects[i].object.fileName;
                        }
                        else if (this.trackedObjects[i].tag == 'road'){
                            this["Hovered Element Information"] = this.trackedObjects[i].object.firstCityLabel + ' to ' + this.trackedObjects[i].object.secondCityLabel + '. Width :' + this.trackedObjects[i].object.routeWidth;
                            firstHighlightedCity = this.trackedObjects[i].object.firstCityLabel;
                            secondHighlightedCity = this.trackedObjects[i].object.secondCityLabel
                            
                        }
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
                        if (!(this.trackedObjects[i].object.uuid in this.hardColored) || this.hardColored[this.trackedObjects[i].object.uuid] == false){
                            this.trackedObjects[i].object.material.color.set(this.trackedObjects[i].object.initialColor);
                        }
                    }
                    
                }

                for (let j=0; j<this.cities.length; j++){
                    if (this.cities[j].cityLabel == firstHighlightedCity || this.cities[j].cityLabel == secondHighlightedCity){
                        this.cities[j].meshes.cityGround.material.color.set(0xffff00);
                    } else {
                        if (!(this.cities[j].meshes.cityGround.uuid in this.hardColored) || this.hardColored[this.cities[j].meshes.cityGround.uuid] == false){
                            this.cities[j].meshes.cityGround.material.color.set('grey');
                        }
                        
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

    untrackElement(object) {
        for (let i=0; i < this.trackedObjects.length; i++){
            if (this.trackedObjects[i].object.parent.uuid == object.uuid){
                this.trackedObjects.splice(i, 1);
            }
        }
    }

    getClosestObject(event, mouse, container, raycaster, camera) {
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

        return closestObject;
    }

    resetHardColored(){
        for (let j=0; j<this.cities.length; j++){
            this.cities[j].meshes.cityGround.material.color.set('grey');
            this.hardColored[this.cities[j].meshes.cityGround.uuid] = false;
        }

        for(let j=0; j<this.trackedObjects.length; j++){
            this.trackedObjects[j].object.material.color.set(this.trackedObjects[j].object.initialColor);
            this.hardColored[this.trackedObjects[j].object.uuid] = false;
        }
    }


  }
  
  export { MouseRaycaster };