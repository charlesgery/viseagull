import { getPrimeFactors } from '../../helpers/arithmetic.js'

function getCityGroundDimensions(numberBuildings) {

    if (numberBuildings == 1){
        return [1, 1];
    }
    else {
        const primeFactors = getPrimeFactors(numberBuildings);

        var width = 1;
        var height = 1;

        for(let i=primeFactors.length - 1; i >= 0; i--){
            if(width <= height){
                width *= primeFactors[i];
            }else{
                height *= primeFactors[i];
            }
        }

        const cityGroundDimensions = [width, height];

        return cityGroundDimensions;
    }

}

export { getCityGroundDimensions };