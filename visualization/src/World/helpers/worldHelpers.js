function getMinMaxBuildingSize(citiesData){

    var maxBuildingSize = 0;
    var minBuildingSize = null;
    for(let i=0; i < citiesData.length; i++){
      for(let j=0; j < citiesData[i].buildings.length; j++){
        if (citiesData[i].buildings[j].height > maxBuildingSize) {
          maxBuildingSize = citiesData[i].buildings[j].height;
        }
        if (minBuildingSize == null || citiesData[i].buildings[j].height < minBuildingSize) {
          minBuildingSize = citiesData[i].buildings[j].height;
        }
      }
    }

    return {maxBuildingSize, minBuildingSize};
}

function getMinMaxDate(filesModificationsDates, dateType){

    var minDate = null;
    var maxDate = null;
    for(let key in filesModificationsDates){

        var date;
        if (dateType == "last_modification"){
            date = new Date(filesModificationsDates[key].last_modification);
        } else if (dateType == "creation_date"){
            date = new Date(filesModificationsDates[key].creation_date);
        }

        var timestamp = date.getTime();

        if (minDate == null || timestamp < minDate) {
            minDate = timestamp;
        }
        if (maxDate == null || timestamp > maxDate) {
            maxDate = timestamp;
        }

    }
    
    var minMaxDate = {min : minDate, max : maxDate};

    return minMaxDate;
}

export {getMinMaxBuildingSize, getMinMaxDate};