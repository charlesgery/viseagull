import { Raycaster, Vector2 } from 'https://unpkg.com/three@0.127.0/build/three.module.js';

const setSize = (container, camera, renderer) => {
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
  
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
  };
  
  class MouseRaycaster {
    constructor(container, camera, commitToFiles, cities, url, activeBranch) {

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
            var filesNames = [];

            for(let i=0; i<this.trackedObjects.length; i++){


                if (closestObject != null && this.trackedObjects[i].object.uuid == closestObject.uuid) {

                    if (this.trackedObjects[i].tag == 'building'){

                        this.resetHardColored()
                        
                        clickedOnBuilding = true;
                        var parentCityLabel = this.trackedObjects[i].object.parent.cityLabel;
                        
                        for (let j=0; j<this.cities.length; j++){
                            if (this.cities[j].cityLabel == parentCityLabel){
                                this.cities[j].meshes.cityGround.material.color.set(0xffff00);
                                this.hardColored[this.cities[j].meshes.cityGround.uuid] = true;

                                var city = this.cities[j];
                                for (let j=0; j<city.meshes.buildings.length; j++){
                                    filesNames.push(city.meshes.buildings[j].fileName);
                                }
                                filesNames.sort();
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

            var clusterFilesBox = document.getElementById("cluster-files");
            this.resetClusterFilesList();

            if (!clickedOnBuilding) {
                // set all elements to their initial color
                clusterFilesBox.style.padding = "0px";
                clusterFilesBox.style.border = "0px solid yellow";
                this.resetHardColored()
            } else {
                clusterFilesBox.style.padding = "10px";
                clusterFilesBox.style.border = "2px solid yellow";
                var ul = document.createElement("ul");
                for (let i=0; i<filesNames.length; i++){
                    var li = document.createElement("li");
                    var textNode = document.createTextNode(filesNames[i]);
                    li.appendChild(textNode);
                    ul.appendChild(li);
                }

                clusterFilesBox.appendChild(ul);
            }



        });
  
        window.addEventListener('mousemove', (event) => {


            var closestObject = this.getClosestObject(event, mouse, container, raycaster, camera);

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
                            this["Hovered Element Information"] = 'Width :' + this.trackedObjects[i].object.routeWidth;
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
                            if (this.isNotHardColored(this.trackedObjects[i].object)){
                                this.trackedObjects[i].object.material.color.set(this.trackedObjects[i].object.initialColor); 
                            }
                        }
                    } else {
                        if (this.isNotHardColored(this.trackedObjects[i].object)){
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

        window.addEventListener('dblclick', (event) => {

            if (activeBranch !== null){
                var closestObject = this.getClosestObject(event, mouse, container, raycaster, camera);
                var clickedOnBuilding = false;

                for(let i=0; i<this.trackedObjects.length; i++){

                    if (closestObject != null && this.trackedObjects[i].object.uuid == closestObject.uuid) {
    
                        if (this.trackedObjects[i].tag == 'building'){
                            
                            clickedOnBuilding = true;

                            window.open(
                                url + '/blob/' + activeBranch + '/' + closestObject.fileName, "_blank");
                            
    
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
        if(commit != 'None') this.highlightedCommit = commit;
        else this.highlightedCommit = null;
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

    isNotHardColored(object){
        return !(object.uuid in this.hardColored) || this.hardColored[object.uuid] == false;
    }

    resetClusterFilesList(){
        var clusterFilesBox = document.getElementById("cluster-files");
        if(clusterFilesBox.childNodes.length > 0){
            var list = clusterFilesBox.childNodes[0];
            clusterFilesBox.removeChild(list);
        } 
    }


  }
  
  export { MouseRaycaster };