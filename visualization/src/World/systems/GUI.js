import * as dat from 'https://unpkg.com/dat.gui@0.7.7/build/dat.gui.module.js';
import { getMinMaxDate } from '../helpers/worldHelpers.js';


class GUI {


    constructor(cities, filesModificationsDates, mouseRaycaster, routes){

        this.gui = new dat.GUI({name: 'Couplings Visualization'});

        var parameters = {
            buildingColor : "base",
            hovered : "",
            highlightedCommit : "",
            routeSlider : 0
        }

        this.buildingColor = this.gui.add(parameters, "buildingColor", ["base", "creation_date", "last_modification"]);
        this.buildingColor.onChange(function(value){
            updateBuildingColor(value, cities, filesModificationsDates);
        });

        this.highlightedCommit = this.gui.add(parameters, "highlightedCommit");
        this.highlightedCommit.onChange(function(value){
            mouseRaycaster.updateHighlightedCommit(value);
        });

        for (let i=0; i<routes.length; i++){
            
        }

        this.hovered = this.gui.add(mouseRaycaster, "hoveredObjectData").listen();

        this.routeSlider = this.gui.add(parameters, "routeSlider", 0, 100);

        this.gui.width = 500;

        this.gui.open();


    };

    
}

function updateBuildingColor(value, cities, filesModificationsDates){

    var minMaxDate = null;
    if (value != 'base'){
        var minMaxDate = getMinMaxDate(filesModificationsDates, value);
    }

    for(let i=0; i < cities.length; i++){
        cities[i].updateColor(filesModificationsDates, minMaxDate, value);
    }
};

export { GUI };