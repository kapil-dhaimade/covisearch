function getResourceList()
{
    var resourceList = [
        {
            'displayName': 'Ambulance',
            'value': 'ambulance',
            'image': 'images/icons/ambulance.png'
        },
        {
            'displayName': 'Oxygen',
            'value': 'oxygen',
            'image': 'images/icons/oxygen.png',
            'children': [
                {
                    'displayName': 'All equipments',
                    'value': 'oxygen',
                    'image': 'images/icons/oxygen.png',
                    'category': 'Oxygen Equipment'
                },
                {
                    'displayName': 'Oxygen Concentrator',
                    'value': 'oxy_concentrator',
                    'image': 'images/icons/oxygen.png',
                    'category': 'Oxygen Equipment'
                },
                {
                    'displayName': 'Oxygen Cylinder',
                    'value': 'oxy_cylinder',
                    'image': 'images/icons/oxygen.png',
                    'category': 'Oxygen Equipment'
                },
                {
                    'displayName': 'Oxygen refill',
                    'value': 'oxy_refill',
                    'image': 'images/icons/oxygen.png',
                    'category': 'Oxygen Equipment'
                },
                {
                    'displayName': 'Oxygen Regulator',
                    'value': 'oxy_regulator',
                    'image': 'images/icons/oxygen.png',
                    'category': 'Oxygen Equipment'
                }
            ]
        },
        {
            'displayName': 'Hospital Beds',
            'value': 'hospital_bed',
            'image': 'images/icons/hospital_bed.png'
        },
        {
            'displayName': 'ICU Beds',
            'value': 'hospital_bed_icu',
            'image': 'images/icons/icu.png'
        },
        {
            'displayName': 'ECMO',
            'value': 'ecmo',
            'image': 'images/icons/ecmo.png'
        },
        {
            'displayName': 'Blood',
            'value': 'blood',
            'image': 'images/icons/plasma.png'
        },
        {
            'displayName': 'Food',
            'value': 'food',
            'image': 'images/icons/food.png'
        },
        {
            'displayName': 'Testing',
            'value': 'testing',
            'image': 'images/icons/testing.png'
        },
        {
            'displayName': 'Medicines',
            'value': 'medicine',
            'image': 'images/icons/medicine.png',
            'children': [
                {
                    'displayName': 'All Medicines',
                    'value': 'medicine',
                    'image': 'images/icons/medicine.png',
                    'category': 'Medicine'
                },
                {
                    'displayName': 'Amphotericin B',
                    'value': 'med_amphotericin',
                    'image': 'images/icons/medicine.png',
                    'category': 'Medicine'
                },
				{
                    'displayName': 'Fabiflu',
                    'value': 'med_fabiflu',
                    'image': 'images/icons/medicine.png',
                    'category': 'Medicine'
                },
                {
                    'displayName': 'Cresemba',
                    'value': 'med_cresemba',
                    'image': 'images/icons/medicine.png',
                    'category': 'Medicine'
                },
                {
                    'displayName': 'Tocilizumab',
                    'value': 'med_tocilizumab',
                    'image': 'images/icons/medicine.png',
                    'category': 'Medicine'
                },
                {
                    'displayName': 'Oseltamivir',
                    'value': 'med_oseltamivir',
                    'image': 'images/icons/medicine.png',
                    'category': 'Medicine'
                },
                {
                    'displayName': 'Ampholyn',
                    'value': 'med_ampholyn',
                    'image': 'images/icons/medicine.png',
                    'category': 'Medicine'
                },
                {
                    'displayName': 'Posacanazole',
                    'value': 'med_posaconazole',
                    'image': 'images/icons/medicine.png',
                    'category': 'Medicine'
                }
            ]
        },
        {
            'displayName': 'Ventilator',
            'value': 'ventilator',
            'image': 'images/icons/ventilator.png'
        },
        {
            'displayName': 'Helpline',
            'value': 'helpline',
            'image': 'images/icons/helpline.png'
        },
        {
            'displayName': 'Plasma',
            'value': 'plasma',
            'image': 'images/icons/plasma.png'
        }
    ];

    return resourceList;
}

function getResource(data) {
    resource = ""
    if(data.resource.children)
    {
        resource = data.subresource;
    }
    else
    {
        resource = data.resource;
    }
    return resource;
  }

  function sharingData(filter,x) {
    str = "Found this resource for " + getResource(filter).displayName + " in " + filter.city;

    if (x.contact_name) {
        str = str + "\n*Name:* " + x.contact_name;
    }
    else {
        str = str + "\n*Name:* " + "Not Provided";
    }
    if (x.phones) {
        str = str + "\n*Number:* " + x.phones.join();
    }
    if (x.litres) {
        str = str + "\n*Liters of Oxygen:* " + x.liters;
    }
    if (x.available_no_ventilator_beds != undefined) {
        str = str + "\n*ICU Beds without Ventilators:* " + (x.available_no_ventilator_beds >= 0 ? x.available_no_ventilator_beds : "N.A");
    }
    if (x.available_ventilator_beds != undefined) {
        str = str + "\n*ICU Beds with Ventilators:* " + (x.available_ventilator_beds >= 0 ? x.available_ventilator_beds : "N.A.");
    }
    if (x.total_available_icu_beds != undefined) {
        str = str + "\n*Total ICU beds:* " + (x.total_available_icu_beds >= 0 ? x.total_available_icu_beds : "N.A.");
    }
    if (x.available_no_oxygen_beds != undefined) {
        str = str + "\n*Beds without Oxygen:* " + (x.available_no_oxygen_beds >= 0 ? x.available_no_oxygen_beds : "N.A");
    }
    if (x.available_oxygen_beds != undefined) {
        str = str + "\n*Beds with Oxygen:* " + (x.available_oxygen_beds >= 0 ? x.available_oxygen_beds : "N.A.");
    }
    if (x.available_covid_beds != undefined) {
        str = str + "\n*Beds for Covid:* " + (x.available_covid_beds >= 0 ? x.available_covid_beds : "N.A.");
    }
    if (x.total_available_beds != undefined) {
        str = str + "\n*Total Beds:* " + (x.total_available_beds >= 0 ? x.total_available_beds : "N.A.");
    }
    if (x.address) {
        str = str + "\n*Address:* " + x.address;
    }
    if (x.details) {
        str = str + "\n*Details:* " + x.details;
    }
    if (x.sources) {
        str += "\n*Source:* " + x.sources[0].url;
    }
    str += "\n\nFound by https://www.covisearch.in"
    return str;
}

function copyingData(filter,x) {
    str = "Found this resource for " + getResource(filter).displayName + " in " + filter.city;

    if (x.contact_name) {
        str = str + "\nName: " + x.contact_name;
    }
    else {
        str = str + "\nName: " + "Not Provided";
    }
    if (x.phones) {
        str = str + "\nNumber: " + x.phones.join();
    }
    if (x.litres) {
        str = str + "\nLiters of Oxygen: " + x.liters;
    }
    if (x.available_no_ventilator_beds != undefined) {
        str = str + "\nICU Beds without Ventilators: " + (x.available_no_ventilator_beds >= 0 ? x.available_no_ventilator_beds : "N.A");
    }
    if (x.available_ventilator_beds != undefined) {
        str = str + "\nICU Beds with Ventilators: " + (x.available_ventilator_beds >= 0 ? x.available_ventilator_beds : "N.A.");
    }
    if (x.total_available_icu_beds != undefined) {
        str = str + "\nTotal ICU beds: " + (x.total_available_icu_beds >= 0 ? x.total_available_icu_beds : "N.A.");
    }
    if (x.available_no_oxygen_beds != undefined) {
        str = str + "\nBeds without Oxygen: " + (x.available_no_oxygen_beds >= 0 ? x.available_no_oxygen_beds : "N.A");
    }
    if (x.available_oxygen_beds != undefined) {
        str = str + "\nBeds with Oxygen: " + (x.available_oxygen_beds >= 0 ? x.available_oxygen_beds : "N.A.");
    }
    if (x.available_covid_beds != undefined) {
        str = str + "\nBeds for Covid: " + (x.available_covid_beds >= 0 ? x.available_covid_beds : "N.A.");
    }
    if (x.total_available_beds != undefined) {
        str = str + "\nTotal Beds: " + (x.total_available_beds >= 0 ? x.total_available_beds : "N.A.");
    }
    if (x.address) {
        str = str + "\nAddress: " + x.address;
    }
    if (x.details) {
        str = str + "\nDetails: " + x.details;
    }
    if (x.sources) {
        str += "\nSource: " + x.sources[0].url;
    }
    str += "\n\nFound by https://www.covisearch.in"
    return str;
}

function setNearbyCity(city) {
    selectedCitylocationData = cityLocationData.cities.find(element => element.city.toLowerCase() === city.toLowerCase());
    // For cases whose location is not known yet
    if(typeof selectedCitylocationData !== "undefined"){
        return cityLocationData.cities.sort((a,b) => distance(selectedCitylocationData,a)-distance(selectedCitylocationData,b)).slice(1,6);
    }
    else
    {
        return undefined;
    }
}

function distance(location1, location2) {
    var lat1 = location1.lat, lon1 = location1.lng, lat2 = location2.lat, lon2 = location2.lng
    var radlat1 = Math.PI * lat1/180
    var radlat2 = Math.PI * lat2/180
    var theta = lon1-lon2
    var radtheta = Math.PI * theta/180
    var dist = Math.sin(radlat1) * Math.sin(radlat2) + Math.cos(radlat1) * Math.cos(radlat2) * Math.cos(radtheta);
    if (dist > 1) {
        dist = 1;
    }
    dist = Math.acos(dist)
    dist = dist * 180/Math.PI
    dist = dist * 60 * 1.1515
    // if (unit=="K") { dist = dist * 1.609344 }
    // if (unit=="N") { dist = dist * 0.8684 }
    return dist
}