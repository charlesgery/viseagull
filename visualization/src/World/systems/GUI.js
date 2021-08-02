import * as dat from 'https://unpkg.com/dat.gui@0.7.7/build/dat.gui.module.js';
import { getMinMaxDate } from '../helpers/worldHelpers.js';


class GUI {


    constructor(cities, filesModificationsDates, mouseRaycaster, routes, scene, commitsHashes, url){

        this.routes = routes;

        this.gui = new dat.GUI({name: 'Couplings Visualization'});

        var commit = null;

        var parameters = {
            "Building Color" : "base",
            "Highlight Commit with Hash" : "",
            "Display routes with width >=" : 0
        }

        var buttonCommit = { 'Open Commit in new Tab':function(){
            if (commit !== null && url !== null && commit != 'None'){
                var urlToCommit = url + '/commit/' + commit;
                window.open(urlToCommit, "_blank");
            } else if (url == null){
                alert('Using local repository');
            } else{
                alert('No commit selected');
            }
            
        }};

        var buttonFeedback = { 'Send Feedback':function(){
                window.open("mailto:charles.gery@gmail.com?subject=Feedback%20Viseagull", "_blank");
        }};

        this.buildingColor = this.gui.add(parameters, "Building Color", ["base", "File Creation Date", "File Last Modification Date"]);
        this.buildingColor.onChange(function(value){
            updateBuildingColor(value, cities, filesModificationsDates);
        });

        this.commitFolder = this.gui.addFolder('Display commits')

        this.highlightedCommit = this.commitFolder.add(parameters, "Highlight Commit with Hash", commitsHashes);
        this.highlightedCommit.onChange(function(value){
            mouseRaycaster.updateHighlightedCommit(value);
            commit = value;
        });

        this.commitFolder.add(buttonCommit,'Open Commit in new Tab');

        var maxWidth = 0;
        for (let i=0; i<routes.length; i++){
            if (routes[i].children[0].routeWidth > maxWidth) maxWidth = routes[i].children[0].routeWidth;
        }

        this.hovered = this.gui.add(mouseRaycaster, "Hovered Element Information").listen();

        this.routeSlider = this.gui.add(parameters, "Display routes with width >=", 0, maxWidth);
        this.routeSlider.onChange(function(value){
            updateDisplayedRoutes(value, routes, scene, mouseRaycaster);
        });

        this.gui.add(buttonFeedback,'Send Feedback');

        this.gui.width = 700;

        this.gui.open();


    };

    
}

function updateBuildingColor(value, cities, filesModificationsDates){

    var minMaxDate = null;
    if (value != 'base'){
        var type = "base";
        if (value == "File Creation Date"){
            type = "creation_date";
        } else if (value == "File Last Modification Date"){
            type = "last_modification";
        }
        var minMaxDate = getMinMaxDate(filesModificationsDates, type);
    }

    for(let i=0; i < cities.length; i++){
        cities[i].updateColor(filesModificationsDates, minMaxDate, type);
    }
};

function updateDisplayedRoutes(value, routes, scene, mouseRaycaster){
    for (let i=0; i<routes.length; i++){
        if (routes[i].children[0].routeWidth < value){
            scene.remove(routes[i]);
            mouseRaycaster.untrackElement(routes[i]);
        } else if (routes[i].parent != scene) {
            scene.add(routes[i]);
            mouseRaycaster.add(routes[i].children[0], 'road');
        }
    }

}

export { GUI };