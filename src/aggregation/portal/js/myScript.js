var app = angular.module('myApp', []);
app.controller('formCtrl', function ($scope, $http, $timeout, $window) {
    const api_base_url = "https://asia-south1-covisearch2.cloudfunctions.net/covisearchapi?";
    var list = null;
    $scope.master = {
        city: "Delhi",
        resource: {
            'displayName': 'Oxygen',
            'value': 'oxygen',
            'image': 'images/icons/oxygen.png'
        }
    };
    $scope.screenStatus = 'loading';
    $http.get('../data/cities.txt').then(function (response) {
        list = response.data;
    });

    $scope.init = function () {
        $scope.pageNumber = 0;
        $scope.retryCount = 5;
        // $scope.screenStatus = 'home';
    };

    $scope.resourceList = [
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
            'children':[
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

    $scope.fetch = function (data) {
        resource = ""
        if(data.subresource != undefined)
        {
            resource = data.subresource.value;
        }
        else
        {
            resource = data.resource.value;
        }
        url = api_base_url + "resource_type=" + resource + "&city=" + data.city +
                         "&page_no=" + $scope.pageNumber;
        // url = '../data/api.txt'
        console.log(url)
        $scope.leads = "";
        $scope.hasMoreData = false;
        $http.get(url).then(function (response) {
            $scope.citySearched = data.city;
            $scope.resourceSearched = data.resource;
            if (response.status == 202) {
                if ($scope.retryCount > 0) {
                    $timeout(function () { $scope.fetch(data) }, 2000);
                    $scope.retryCount--;
                    $scope.screenStatus = 'fetchingData';
                    return;
                }
                else {
                    $scope.screenStatus = "timeout";
                    return;
                }
            }
            else {
                $scope.leads = response.data.resource_info_data;
                $scope.hasMoreData = response.data.meta_info.more_data_available;
                $scope.screenStatus = 'dataFetched';
                $window.scrollTo(0, 0);
                return
            }
        },
            function myError(response) {
                $scope.errMessage = response.data;
                $scope.screenStatus = 'error';
            });
    };

    $scope.getFromNowDate = function (date) {
        var now;
        if (date && date.trim()) {
            now = moment(date).fromNow();
        }
        else {
            now = "Not Specified"
        }
        return now;
    };

    $scope.getDate = function (date) {
        var date = moment(date);
        return date.format('DD-MM-YYYY');
    };

    $scope.getNumbers = function (number) {
        var contvertedNum;
        if (number != null && number >= 0) {
            contvertedNum = number;
        }
        else {
            contvertedNum = "N.A."
        }
        return contvertedNum;
    }

    $scope.checkIfHospitalBedICU = function (x) {
        if (x.available_no_ventilator_beds != null
            || x.available_ventilator_beds != null
            || x.total_available_icu_beds != null) {
            return true;
        }
        return false;
    }

    $scope.checkIfHospitalBed = function (x) {
        if (x.available_no_oxygen_beds != null
            || x.available_oxygen_beds != null
            || x.total_available_beds != null
            || x.available_covid_beds != null) {
            return true;
        }
        return false;
    }

    $scope.fetchNextBatch = function (data) {
        if ($scope.hasMoreData == true || $scope.pageNumber == 0) {
            $scope.pageNumber += 1;
            $scope.screenStatus = 'loading';
            $scope.fetch($scope.master);
        }
    };

    $scope.fetchPreviousBatch = function (data) {
        if ($scope.pageNumber > 1) {
            $scope.pageNumber -= 1;
            $scope.screenStatus = 'loading';
            $scope.fetch($scope.master);
        }
    };

    $scope.submit = function () {
        $scope.init();
        $scope.screenStatus = 'loading';
        $scope.master = angular.copy($scope.filter);
        $scope.fetchNextBatch($scope.master);
    };

    $scope.filterFunction = function () {
        if ($scope.filter.city) {
            var filter = $scope.filter.city.toLowerCase();
            var filterList = list.filter((country) => country.startsWith(filter));
            $scope.cityList = filterList.slice(0, 3);
        }
    };

    $scope.onPageLoad = function () {
        $scope.init();
        $scope.screenStatus = 'loading';
        $scope.fetchNextBatch($scope.master);
    }

    $scope.sharingData = function (x) {
        str = "";
        if (x.contact_name) {
            str = str + "Name: " + x.contact_name;
        }
        else {
            str = str + "Name: " + "Not Provided";
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
        return str;
    }
    $scope.copy = function (x) {
        const el = document.createElement('textarea');
        var str = $scope.sharingData(x);
        el.value = str;
        document.body.appendChild(el);
        el.select();
        document.execCommand('copy');
        document.body.removeChild(el);
    };

    $scope.share = function (x) {
        var str = $scope.sharingData(x);

        window.location.href = "whatsapp://send?text=" + encodeURIComponent(str);
    };

    $scope.init();
    $scope.onPageLoad();
});

